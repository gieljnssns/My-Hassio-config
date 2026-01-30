# thermal_analysis.py
# Place this in: config/python_scripts/thermal_analysis.py

# Haal historische data op via recorder statistics service
def get_historical_data(entity_id, hours=24, apply_cop=False, cop_value=4.66):
    """Haal historische data op voor een entity via recorder statistics"""
    try:
        # dt_util is al beschikbaar als variabele (geen import nodig!)
        # Bereken start tijd
        end_time = dt_util.now()  # noqa: F821
        start_time = end_time - datetime.timedelta(hours=hours)  # noqa: F821
        
        # Gebruik recorder.get_statistics service
        # Deze service returnt de data direct
        service_data = {
            'statistic_ids': [entity_id],
            'period': '5minute',
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'types': ['mean']
        }
        
        logger.info(f"Ophalen statistieken voor {entity_id} vanaf {start_time.isoformat()}")  # noqa: F821
        
        # Roep de service aan via hass.services
        result = hass.services.call('recorder', 'get_statistics', service_data, blocking=True, return_response=True)  # noqa: F821
        
        values = []
        # De data zit in result['statistics'][entity_id]
        if result and 'statistics' in result and entity_id in result['statistics']:
            for stat in result['statistics'][entity_id]:
                if stat.get('mean') is not None:
                    value = float(stat['mean'])
                    if apply_cop:
                        value = value * cop_value
                    values.append(value)
        
        logger.info(f"Opgehaald: {len(values)} datapunten voor {entity_id}")  # noqa: F821
        return values
        
    except Exception as e:
        logger.error(f"Fout bij ophalen data voor {entity_id}: {str(e)}")  # noqa: F821
        return []

def calculate_thermal_inertia():
    """Bereken thermische inertie op basis van temperatuur response"""
    
    logger.info("Start thermische analyse...")  # noqa: F821
    
    # Haal data op - elektrisch vermogen wordt direct omgezet naar thermisch
    temp_inside = get_historical_data('sensor.gemiddelde_temp_beneden', 24)
    temp_outside = get_historical_data('sensor.buiten_temperatuur', 24)
    power_data = get_historical_data('sensor.warmtepomp_huidig_verbruik', 24, apply_cop=True, cop_value=4.66)
    
    logger.info(f"Data opgehaald - Inside: {len(temp_inside)}, Outside: {len(temp_outside)}, Power: {len(power_data)}")
    
    if len(temp_inside) < 10 or len(temp_outside) < 10 or len(power_data) < 10:
        logger.warning("Niet genoeg data voor thermische analyse")
        logger.warning(f"Inside temp: {len(temp_inside)}, Outside temp: {len(temp_outside)}, Power: {len(power_data)}")
        return
    
    # Synchroniseer de data lengths (neem kortste lengte)
    min_length = min(len(temp_inside), len(temp_outside), len(power_data))
    temp_inside = temp_inside[:min_length]
    temp_outside = temp_outside[:min_length]
    power_data = power_data[:min_length]
    
    logger.info(f"Gesynchroniseerde data length: {min_length}")
    
    # Bereken warmteverlies coëfficiënt voor elke meting
    heat_loss_data = []
    for i in range(len(power_data)):
        delta_t = temp_inside[i] - temp_outside[i]
        if delta_t > 0 and power_data[i] > 500:  # Alleen als warmtepomp actief is
            heat_loss_coeff = power_data[i] / delta_t
            heat_loss_data.append({
                'coefficient': heat_loss_coeff,
                'outside_temp': temp_outside[i],
                'inside_temp': temp_inside[i],
                'power': power_data[i],
                'delta_t': delta_t
            })
    
    logger.info(f"Warmteverlies metingen gevonden: {len(heat_loss_data)}")
    
    # Zoek periodes waar warmtepomp aan/uit gaat
    thermal_responses = []
    
    for i in range(1, len(power_data) - 12):  # -12 zodat we vooruit kunnen kijken
        # Warmtepomp start (van <500W thermisch naar >2000W thermisch)
        if power_data[i-1] < 500 and power_data[i] > 2000:
            start_temp = temp_inside[i]
            start_power = power_data[i]
            start_outside = temp_outside[i]
            
            # Vind steady state temperatuur
            for j in range(i+1, min(i+36, len(temp_inside))):  # Max 3 uur vooruit
                if j > 0 and abs(temp_inside[j] - temp_inside[j-1]) < 0.05:  # Stabiel
                    end_temp = temp_inside[j]
                    time_to_stable = (j - i) * 5  # 5 minuten per datapunt
                    
                    if time_to_stable > 15 and end_temp > start_temp:  # Minimaal 15 minuten
                        thermal_responses.append({
                            'time_constant': time_to_stable * 0.63,
                            'temp_rise': end_temp - start_temp,
                            'outside_temp': start_outside,
                            'power': start_power
                        })
                    break
    
    logger.info(f"Thermal responses gevonden: {len(thermal_responses)}")
    
    # Bereken gemiddelde tijdconstante (als beschikbaar)
    avg_time_constant = 60  # Default waarde in minuten
    if thermal_responses:
        avg_time_constant = sum(r['time_constant'] for r in thermal_responses) / len(thermal_responses)
        logger.info(f"Gemiddelde tijdconstante: {avg_time_constant:.1f} minuten")
    
    # Bereken warmteverlies coëfficiënt per buitentemperatuur
    heat_loss_coefficients = {}
    
    # Gebruik alle heat_loss_data
    for data_point in heat_loss_data:
        outside_temp_rounded = round(data_point['outside_temp'])
        
        if outside_temp_rounded not in heat_loss_coefficients:
            heat_loss_coefficients[outside_temp_rounded] = []
        heat_loss_coefficients[outside_temp_rounded].append(data_point['coefficient'])
    
    # Gemiddelde per buitentemperatuur
    avg_coefficients = {}
    for temp in sorted(heat_loss_coefficients.keys()):
        coeffs = heat_loss_coefficients[temp]
        avg_coefficients[str(temp)] = round(sum(coeffs) / len(coeffs), 2)
    
    logger.info(f"Warmteverlies coëfficiënten berekend voor {len(avg_coefficients)} temperaturen")
    
    # Sla resultaten op als sensor attributes
    current_time = dt_util.now().isoformat()
    
    hass.states.set(
        'sensor.thermische_analyse_resultaten',
        round(avg_time_constant, 1),
        {
            'unit_of_measurement': 'minuten',
            'friendly_name': 'Thermische Tijdconstante',
            'warmteverlies_coefficienten': avg_coefficients,
            'aantal_metingen': len(heat_loss_data),
            'aantal_thermal_responses': len(thermal_responses),
            'laatste_update': current_time,
            'cop_gebruikt': 4.66
        }
    )
    
    # Bereken runtime per buitentemperatuur voor gewenste temperatuurstijging
    runtime_predictions = {}
    detailed_predictions = {}
    
    target_temp_rise = 1.0  # 1°C temperatuurstijging
    target_inside_temp = 20.0  # Gewenste binnentemperatuur
    
    for temp_str, coeff in avg_coefficients.items():
        outside_temp = int(temp_str)
        # Geschat vermogen nodig bij deze buitentemperatuur
        delta_t = target_inside_temp - outside_temp
        if delta_t > 0:
            required_power = coeff * delta_t
            
            # Runtime schatting voor 1°C stijging
            if required_power > 0:
                estimated_runtime = (avg_time_constant * target_temp_rise) * 1.2  # 20% marge
                runtime_predictions[temp_str] = round(estimated_runtime, 1)
                
                # Voeg gedetailleerde info toe
                detailed_predictions[temp_str] = {
                    'runtime_minuten': round(estimated_runtime, 1),
                    'warmteverlies_coeff': coeff,
                    'benodigd_vermogen_W': round(required_power, 0),
                    'elektrisch_vermogen_W': round(required_power / 4.66, 0),
                    'kosten_per_uur_euro': round((required_power / 4.66 / 1000) * 0.30, 3)  # Aanname: €0.30/kWh
                }
    
    hass.states.set(
        'sensor.warmtepomp_runtime_voorspelling',
        len(runtime_predictions),
        {
            'unit_of_measurement': 'temperaturen',
            'friendly_name': 'Warmtepomp Runtime Voorspelling',
            'runtime_per_buitentemp_minuten': runtime_predictions,
            'gedetailleerde_voorspelling': detailed_predictions,
            'voor_temperatuurstijging': f"{target_temp_rise}°C",
            'naar_binnentemperatuur': f"{target_inside_temp}°C",
            'laatste_update': current_time,
            'gebaseerd_op_metingen': len(heat_loss_data),
            'uitleg': 'Runtime is de geschatte tijd die de warmtepomp nodig heeft om de temperatuur met 1°C te verhogen bij de gegeven buitentemperatuur'
        }
    )
    
    # Maak ook een praktische sensor voor de huidige situatie
    current_outside_temp = round(float(hass.states.get('sensor.buiten_temperatuur').state))
    current_inside_temp = float(hass.states.get('sensor.gemiddelde_temp_beneden').state)
    
    if str(current_outside_temp) in avg_coefficients:
        current_coeff = avg_coefficients[str(current_outside_temp)]
        current_delta = target_inside_temp - current_inside_temp
        
        if current_delta > 0:
            current_required_power = current_coeff * (target_inside_temp - current_outside_temp)
            current_runtime = (avg_time_constant * current_delta) * 1.2
            
            hass.states.set(
                'sensor.warmtepomp_huidige_voorspelling',
                round(current_runtime, 1),
                {
                    'unit_of_measurement': 'minuten',
                    'friendly_name': 'Warmtepomp Runtime Nu',
                    'buitentemperatuur': current_outside_temp,
                    'binnentemperatuur': current_inside_temp,
                    'doel_temperatuur': target_inside_temp,
                    'temperatuur_te_verhogen': round(current_delta, 1),
                    'benodigd_thermisch_vermogen_W': round(current_required_power, 0),
                    'benodigd_elektrisch_vermogen_W': round(current_required_power / 4.66, 0),
                    'geschatte_kosten_euro': round((current_required_power / 4.66 / 1000) * (current_runtime / 60) * 0.30, 2),
                    'laatste_update': current_time
                }
            )
    
    # Log samenvatting
    logger.info("=== Thermische Analyse Compleet ===")
    logger.info(f"Tijdconstante: {avg_time_constant:.1f} minuten")
    logger.info(f"Thermal responses: {len(thermal_responses)}")
    logger.info(f"Heat loss metingen: {len(heat_loss_data)}")
    logger.info(f"Runtime voorspellingen voor {len(runtime_predictions)} temperaturen")

# Main execution
try:
    if data.get('calculate_time_constant'):
        calculate_thermal_inertia()
    else:
        logger.info("Thermal analysis script aangeroepen zonder parameters")
except Exception as e:
    logger.error(f"Fout in thermal analysis: {str(e)}")
# # thermal_analysis.py
# # Place this in: config/python_scripts/thermal_analysis.py

# # Haal historische data op via recorder statistics service
# def get_historical_data(entity_id, hours=24, apply_cop=False, cop_value=4.66):
#     """Haal historische data op voor een entity via recorder statistics"""
#     try:
#         # dt_util is al beschikbaar als variabele (geen import nodig!)
#         # Bereken start tijd
#         end_time = dt_util.now()
#         start_time = end_time - datetime.timedelta(hours=hours)
        
#         # Gebruik recorder.get_statistics service
#         # Deze service returnt de data direct
#         service_data = {
#             'statistic_ids': [entity_id],
#             'period': '5minute',
#             'start_time': start_time.isoformat(),
#             'end_time': end_time.isoformat(),
#             'types': ['mean']
#         }
        
#         logger.warning(f"Ophalen statistieken voor {entity_id} vanaf {start_time.isoformat()}")
        
#         # Roep de service aan
#         # De service response komt terug als dictionary
#         result = hass.services.call('recorder', 'get_statistics', service_data, blocking=True, return_response=True)

        
#         values = []
#         if result and 'statistics' in result and entity_id in result['statistics']:
#             for stat in result['statistics'][entity_id]:
#                 if stat.get('mean') is not None:
#                     value = float(stat['mean'])
#                     if apply_cop:
#                         value = value * cop_value
#                     values.append(value)
        
#         logger.info(f"Opgehaald: {len(values)} datapunten voor {entity_id}")
#         return values
        
#     except Exception as e:
#         logger.error(f"Fout bij ophalen data voor {entity_id}: {str(e)}")
#         return []

# def calculate_thermal_inertia():
#     """Bereken thermische inertie op basis van temperatuur response"""
    
#     logger.info("Start thermische analyse...")
    
#     # Haal data op - elektrisch vermogen wordt direct omgezet naar thermisch
#     temp_inside = get_historical_data('sensor.gemiddelde_temp_beneden', 24)
#     temp_outside = get_historical_data('sensor.buiten_temperatuur', 24)
#     power_data = get_historical_data('sensor.warmtepomp_huidig_verbruik', 24, apply_cop=True, cop_value=4.66)
    
#     logger.info(f"Data opgehaald - Inside: {len(temp_inside)}, Outside: {len(temp_outside)}, Power: {len(power_data)}")
    
#     if len(temp_inside) < 10 or len(temp_outside) < 10 or len(power_data) < 10:
#         logger.warning("Niet genoeg data voor thermische analyse")
#         logger.warning(f"Inside temp: {len(temp_inside)}, Outside temp: {len(temp_outside)}, Power: {len(power_data)}")
#         return
    
#     # Synchroniseer de data lengths (neem kortste lengte)
#     min_length = min(len(temp_inside), len(temp_outside), len(power_data))
#     temp_inside = temp_inside[:min_length]
#     temp_outside = temp_outside[:min_length]
#     power_data = power_data[:min_length]
    
#     logger.warning(f"Gesynchroniseerde data length: {min_length}")
    
#     # Bereken warmteverlies coëfficiënt voor elke meting
#     heat_loss_data = []
#     for i in range(len(power_data)):
#         delta_t = temp_inside[i] - temp_outside[i]
#         if delta_t > 0 and power_data[i] > 500:  # Alleen als warmtepomp actief is
#             heat_loss_coeff = power_data[i] / delta_t
#             heat_loss_data.append({
#                 'coefficient': heat_loss_coeff,
#                 'outside_temp': temp_outside[i],
#                 'inside_temp': temp_inside[i],
#                 'power': power_data[i],
#                 'delta_t': delta_t
#             })
    
#     logger.warning(f"Warmteverlies metingen gevonden: {len(heat_loss_data)}")
    
#     # Zoek periodes waar warmtepomp aan/uit gaat
#     thermal_responses = []
    
#     for i in range(1, len(power_data) - 12):  # -12 zodat we vooruit kunnen kijken
#         # Warmtepomp start (van <500W thermisch naar >2000W thermisch)
#         if power_data[i-1] < 500 and power_data[i] > 2000:
#             start_temp = temp_inside[i]
#             start_power = power_data[i]
#             start_outside = temp_outside[i]
            
#             # Vind steady state temperatuur
#             for j in range(i+1, min(i+36, len(temp_inside))):  # Max 3 uur vooruit
#                 if j > 0 and abs(temp_inside[j] - temp_inside[j-1]) < 0.05:  # Stabiel
#                     end_temp = temp_inside[j]
#                     time_to_stable = (j - i) * 5  # 5 minuten per datapunt
                    
#                     if time_to_stable > 15 and end_temp > start_temp:  # Minimaal 15 minuten
#                         thermal_responses.append({
#                             'time_constant': time_to_stable * 0.63,
#                             'temp_rise': end_temp - start_temp,
#                             'outside_temp': start_outside,
#                             'power': start_power
#                         })
#                     break
    
#     logger.warning(f"Thermal responses gevonden: {len(thermal_responses)}")
    
#     # Bereken gemiddelde tijdconstante (als beschikbaar)
#     avg_time_constant = 60  # Default waarde in minuten
#     if thermal_responses:
#         avg_time_constant = sum(r['time_constant'] for r in thermal_responses) / len(thermal_responses)
#         logger.warning(f"Gemiddelde tijdconstante: {avg_time_constant:.1f} minuten")
    
#     # Bereken warmteverlies coëfficiënt per buitentemperatuur
#     heat_loss_coefficients = {}
    
#     # Gebruik alle heat_loss_data
#     for data_point in heat_loss_data:
#         outside_temp_rounded = round(data_point['outside_temp'])
        
#         if outside_temp_rounded not in heat_loss_coefficients:
#             heat_loss_coefficients[outside_temp_rounded] = []
#         heat_loss_coefficients[outside_temp_rounded].append(data_point['coefficient'])
    
#     # Gemiddelde per buitentemperatuur
#     avg_coefficients = {}
#     for temp in sorted(heat_loss_coefficients.keys()):
#         coeffs = heat_loss_coefficients[temp]
#         avg_coefficients[str(temp)] = round(sum(coeffs) / len(coeffs), 2)
    
#     logger.warning(f"Warmteverlies coëfficiënten berekend voor {len(avg_coefficients)} temperaturen")
    
#     # Sla resultaten op als sensor attributes
#     current_time = dt_util.now().isoformat()
    
#     hass.states.set(
#         'sensor.thermische_analyse_resultaten',
#         round(avg_time_constant, 1),
#         {
#             'unit_of_measurement': 'minuten',
#             'friendly_name': 'Thermische Tijdconstante',
#             'warmteverlies_coefficienten': avg_coefficients,
#             'aantal_metingen': len(heat_loss_data),
#             'aantal_thermal_responses': len(thermal_responses),
#             'laatste_update': current_time,
#             'cop_gebruikt': 4.66
#         }
#     )
    
#     # Bereken runtime per buitentemperatuur voor gewenste temperatuurstijging
#     runtime_predictions = {}
#     target_temp_rise = 1.0  # 1°C temperatuurstijging
#     target_inside_temp = 20.0  # Gewenste binnentemperatuur
    
#     for temp_str, coeff in avg_coefficients.items():
#         outside_temp = int(temp_str)
#         # Geschat vermogen nodig bij deze buitentemperatuur
#         delta_t = target_inside_temp - outside_temp
#         if delta_t > 0:
#             required_power = coeff * delta_t
            
#             # Runtime schatting voor 1°C stijging
#             if required_power > 0:
#                 estimated_runtime = (avg_time_constant * target_temp_rise) * 1.2  # 20% marge
#                 runtime_predictions[temp_str] = round(estimated_runtime, 1)
    
#     hass.states.set(
#         'sensor.warmtepomp_runtime_voorspelling',
#         len(runtime_predictions),
#         {
#             'unit_of_measurement': 'temperaturen',
#             'friendly_name': 'Warmtepomp Runtime Voorspelling',
#             'runtime_per_buitentemp_minuten': runtime_predictions,
#             'voor_temperatuurstijging': f"{target_temp_rise}°C",
#             'naar_binnentemperatuur': f"{target_inside_temp}°C",
#             'laatste_update': current_time,
#             'gebaseerd_op_metingen': len(heat_loss_data)
#         }
#     )
    
#     # Log samenvatting
#     logger.warning("=== Thermische Analyse Compleet ===")
#     logger.warning(f"Tijdconstante: {avg_time_constant:.1f} minuten")
#     logger.warning(f"Thermal responses: {len(thermal_responses)}")
#     logger.warning(f"Heat loss metingen: {len(heat_loss_data)}")
#     logger.warning(f"Runtime voorspellingen voor {len(runtime_predictions)} temperaturen")

# # Main execution
# try:
#     if data.get('calculate_time_constant'):
#         calculate_thermal_inertia()
#     else:
#         logger.warning("Thermal analysis script aangeroepen zonder parameters")
# except Exception as e:
#     logger.error(f"Fout in thermal analysis: {str(e)}")
