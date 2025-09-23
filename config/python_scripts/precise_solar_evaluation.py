# /config/python_scripts/precise_solar_evaluation.py
"""
Precisie evaluatie script voor solar voorspellingen
Berekent MSE, MAE, RMSE en MAPE voor alle predictors
"""

# # import json
# import math
# # from datetime import datetime, timedelta
# import datetime

def calculate_mse(actual, predicted):
    """Bereken Mean Squared Error"""
    if not actual or not predicted:
        return float('inf')
    
    min_length = min(len(actual), len(predicted))
    if min_length == 0:
        return float('inf')
    
    actual_slice = actual[:min_length]
    predicted_slice = predicted[:min_length]
    
    mse = sum((a - p) ** 2 for a, p in zip(actual_slice, predicted_slice)) / min_length
    return mse

def calculate_mae(actual, predicted):
    """Bereken Mean Absolute Error"""
    if not actual or not predicted:
        return float('inf')
    
    min_length = min(len(actual), len(predicted))
    if min_length == 0:
        return float('inf')
    
    actual_slice = actual[:min_length]
    predicted_slice = predicted[:min_length]
    
    mae = sum(abs(a - p) for a, p in zip(actual_slice, predicted_slice)) / min_length
    return mae

def calculate_rmse(mse_value):
    """Bereken Root Mean Squared Error"""
    # return math.sqrt(mse_value) if mse_value != float('inf') else float('inf')
    return mse_value ** 0.5 if mse_value != float('inf') else float('inf')

def calculate_mape(actual, predicted):
    """Bereken Mean Absolute Percentage Error"""
    if not actual or not predicted:
        return float('inf')
    
    min_length = min(len(actual), len(predicted))
    if min_length == 0:
        return float('inf')
    
    actual_slice = actual[:min_length]
    predicted_slice = predicted[:min_length]
    
    # Filter nullen uit voor MAPE berekening
    valid_pairs = [(a, p) for a, p in zip(actual_slice, predicted_slice) if a != 0]
    
    if not valid_pairs:
        return float('inf')
    
    mape = sum(abs((a - p) / a) for a, p in valid_pairs) / len(valid_pairs) * 100
    return mape

def extract_statistics_values(statistics_data):
    """Extraheer mean waarden uit statistics response"""
    try:
        stats_root = statistics_data.get('statistics', statistics_data)
        sensor_stats = stats_root.get('sensor.huidige_opbrengst_gefilterd', [])
        return [entry.get('mean', 0) for entry in sensor_stats if entry.get('mean') is not None]
    except (AttributeError, TypeError, KeyError):
        logger.warning("Kon statistics data niet parsen")
        return []

def get_history_data(entity_id, attribute_name):
    """Haal history data op van een sensor attribute"""
    try:
        entity_state = hass.states.get(entity_id)
        if entity_state and entity_state.attributes:
            history_data = entity_state.attributes.get(attribute_name, [])
            return [float(x) for x in history_data if x is not None]
        return []
    except (ValueError, TypeError):
        logger.warning(f"Kon {attribute_name} data niet ophalen van {entity_id}")
        return []

def log_evaluation_results(results, best_predictor):
    """Log evaluatie resultaten"""
    current_time = hass.states.get("sensor.time").state
    log_message = f"{current_time}: {best_predictor} (MSE: {results[best_predictor]['mse']:.2f})"
    
    # Update evaluatie log
    hass.services.call('input_text', 'set_value', {
        'entity_id': 'input_text.evaluation_log',
        'value': log_message
    })
    
    # Update laatste evaluatie tijd
    hass.services.call('input_datetime', 'set_datetime', {
        'entity_id': 'input_datetime.last_evaluation_time',
        'datetime': hass.states.get("sensor.date_time_iso").state
    })

# MAIN EXECUTION
try:
    # Haal input parameters op
    statistics_data = data.get('statistics_data', {})
    current_time_str = data.get('current_time', hass.states.get("sensor.date_time_iso").state)
    
    logger.info(f"Starting solar evaluation at {current_time_str}")
    # logger.error(f"Type van statistics_data: {type(statistics_data)}")
    # logger.error(f"Inhoud: {statistics_data}")
    # Extraheer werkelijke data
    real_data = extract_statistics_values(statistics_data)
    
    if not real_data:
        logger.error("Geen werkelijke statistics data beschikbaar")
        hass.services.call('input_text', 'set_value', {
            'entity_id': 'input_text.evaluation_log',
            'value': f"{hass.states.get("sensor.time").state}: Geen data beschikbaar"
        })
    else:
        logger.info(f"Werkelijke data punten: {len(real_data)}")
        
        # Haal alle voorspelling data op
        predictors = {
            'solcast': {
                'history': get_history_data('sensor.solcast_pv_list', 'history'),
                'display_name': 'Solcast'
            },
            'solcast10': {
                'history': get_history_data('sensor.solcast_pv_list', 'history10'), 
                'display_name': 'Solcast 10%'
            },
            'solcast90': {
                'history': get_history_data('sensor.solcast_pv_list', 'history90'),
                'display_name': 'Solcast 90%'
            },
            'openmeteo': {
                'history': get_history_data('sensor.openmeteo_pv_list', 'history'),
                'display_name': 'OpenMeteo'
            }
        }
        
        # Bereken metriek voor elke voorspeller
        results = {}
        
        for predictor_key, predictor_info in predictors.items():
            history_data = predictor_info['history']
            
            if history_data:
                mse = calculate_mse(real_data, history_data)
                mae = calculate_mae(real_data, history_data)
                rmse = calculate_rmse(mse)
                mape = calculate_mape(real_data, history_data)
                
                results[predictor_key] = {
                    'mse': mse,
                    'mae': mae,
                    'rmse': rmse,
                    'mape': mape,
                    'display_name': predictor_info['display_name'],
                    'data_points': min(len(real_data), len(history_data))
                }
                
                logger.info(f"{predictor_info['display_name']}: MSE={mse:.2f}, MAE={mae:.2f}, RMSE={rmse:.2f}, MAPE={mape:.2f}%")
            else:
                logger.warning(f"Geen history data voor {predictor_info['display_name']}")
                results[predictor_key] = {
                    'mse': float('inf'),
                    'mae': float('inf'), 
                    'rmse': float('inf'),
                    'mape': float('inf'),
                    'display_name': predictor_info['display_name'],
                    'data_points': 0
                }
        
        # Update alle input_number entities
        for predictor_key, metrics in results.items():
            # Update MSE
            hass.services.call('input_number', 'set_value', {
                'entity_id': f'input_number.{predictor_key}_mse',
                'value': metrics['mse'] if metrics['mse'] != float('inf') else 999999
            })
            
            # Update MAE
            hass.services.call('input_number', 'set_value', {
                'entity_id': f'input_number.{predictor_key}_mae',
                'value': metrics['mae'] if metrics['mae'] != float('inf') else 999999
            })
        
        # Bepaal beste voorspeller (laagste MSE)
        valid_results = {k: v for k, v in results.items() if v['mse'] != float('inf')}
        
        if valid_results:
            best_predictor_key = min(valid_results.keys(), key=lambda k: valid_results[k]['mse'])
            best_predictor_name = valid_results[best_predictor_key]['display_name']
            
            # Update beste voorspeller alleen als deze anders is
            current_best = hass.states.get('input_text.best_solar_predictor').state
            
            if current_best != best_predictor_key:
                hass.services.call('input_text', 'set_value', {
                    'entity_id': 'input_text.best_solar_predictor',
                    'value': best_predictor_key
                })
                logger.info(f"Beste voorspeller gewijzigd naar: {best_predictor_name}")
            else:
                logger.info(f"Beste voorspeller blijft: {best_predictor_name}")
            
            # Log resultaten
            log_evaluation_results(results, best_predictor_key)
            
            # Optioneel: verstuur persistent notification
            hass.services.call('persistent_notification', 'create', {
                'message': f"""Solar evaluatie voltooid om {hass.states.get("sensor.time").state}

Beste voorspeller: **{best_predictor_name}** (MSE: {valid_results[best_predictor_key]['mse']:.2f})

Alle scores (MSE):
{"".join([f"- {v['display_name']}: {v['mse']:.2f} (MAE: {v['mae']:.2f})" + chr(10) for v in valid_results.values()])}

Data punten gebruikt: {valid_results[best_predictor_key]['data_points']}""",
                'title': '🌞 Solar Voorspelling Evaluatie',
                'notification_id': 'solar_evaluation_' + hass.states.get("sensor.time_date").state
            })
            
        else:
            logger.error("Geen geldige voorspelling data beschikbaar")
            hass.services.call('input_text', 'set_value', {
                'entity_id': 'input_text.evaluation_log',
                'value': f"{hass.states.get("sensor.time").state}: Geen geldige voorspellingen"
            })

except Exception as e:
    logger.error(f"Fout in solar evaluatie script: {str(e)}")
    hass.services.call('input_text', 'set_value', {
        'entity_id': 'input_text.evaluation_log',
        'value': f"{hass.states.get("sensor.time").state}: Script fout - {str(e)[:50]}"
    })
    
    # Verstuur error notification
    hass.services.call('persistent_notification', 'create', {
        'message': f'Fout in solar evaluatie script: {str(e)}',
        'title': '⚠️ Solar Evaluatie Fout',
        'notification_id': 'solar_evaluation_error'
    })