"""
Solar evaluation script for interpolated 5-minute forecasts.
Calculates MSE, MAE, RMSE, and MAPE for Solcast/OpenMeteo interpolated series.
"""


def calculate_mse(actual, predicted):
    if not actual or not predicted:
        return float("inf")

    min_length = min(len(actual), len(predicted))
    if min_length == 0:
        return float("inf")

    actual_slice = actual[:min_length]
    predicted_slice = predicted[:min_length]

    mse = sum((a - p) ** 2 for a, p in zip(actual_slice, predicted_slice)) / min_length
    return mse


def calculate_mae(actual, predicted):
    if not actual or not predicted:
        return float("inf")

    min_length = min(len(actual), len(predicted))
    if min_length == 0:
        return float("inf")

    actual_slice = actual[:min_length]
    predicted_slice = predicted[:min_length]

    mae = sum(abs(a - p) for a, p in zip(actual_slice, predicted_slice)) / min_length
    return mae


def calculate_rmse(mse_value):
    return mse_value ** 0.5 if mse_value != float("inf") else float("inf")


def calculate_mape(actual, predicted):
    if not actual or not predicted:
        return float("inf")

    min_length = min(len(actual), len(predicted))
    if min_length == 0:
        return float("inf")

    actual_slice = actual[:min_length]
    predicted_slice = predicted[:min_length]

    valid_pairs = [(a, p) for a, p in zip(actual_slice, predicted_slice) if a != 0]

    if not valid_pairs:
        return float("inf")

    mape = (
        sum(abs((a - p) / a) for a, p in valid_pairs) / len(valid_pairs) * 100
    )
    return mape


def extract_statistics_values(statistics_data):
    try:
        stats_root = statistics_data.get("statistics", statistics_data)
        sensor_stats = stats_root.get("sensor.huidige_opbrengst_gefilterd", [])
        return [
            entry.get("mean", 0) for entry in sensor_stats if entry.get("mean") is not None
        ]
    except (AttributeError, TypeError, KeyError):
        logger.warning("Kon statistics data niet parsen")
        return []


def get_interpolated_series(entity_id, attribute_name, current_slot):
    """
    Haal interpolated series op en beperk tot history (tot huidige slot).
    current_slot: 5-minuten slot index sinds middernacht (0-575)
    """
    try:
        entity_state = hass.states.get(entity_id)
        if not entity_state or not entity_state.attributes:
            return []
        raw = entity_state.attributes.get(attribute_name, [])
        if not raw:
            return []
        cleaned = [float(x) for x in raw if x is not None]
        # Beperk tot history: alleen data tot en met huidige slot
        # (slot + 1 omdat slot 0 = eerste 5 minuten, slot 1 = tweede 5 minuten, etc.)
        return cleaned[:current_slot + 1]
    except (ValueError, TypeError):
        logger.warning(f"Kon {attribute_name} data niet ophalen van {entity_id}")
        return []


def log_evaluation_results(results, best_predictor):
    current_time = hass.states.get("sensor.time").state
    log_message = (
        f"{current_time}: {best_predictor} (5m MSE: {results[best_predictor]['mse']:.2f})"
    )

    hass.services.call(
        "input_text",
        "set_value",
        {
            "entity_id": "input_text.evaluation_log_interpolated",
            "value": log_message,
        },
    )

    hass.services.call(
        "input_datetime",
        "set_datetime",
        {
            "entity_id": "input_datetime.last_evaluation_time_interpolated",
            "datetime": hass.states.get("sensor.date_time_iso").state,
        },
    )


try:
    statistics_data = data.get("statistics_data", {})
    current_time_str = data.get(
        "current_time", hass.states.get("sensor.date_time_iso").state
    )

    logger.info(f"Starting interpolated solar evaluation at {current_time_str}")
    real_data = extract_statistics_values(statistics_data)

    if not real_data:
        logger.error("Geen werkelijke statistics data beschikbaar voor 5m evaluatie")
        hass.services.call(
            "input_text",
            "set_value",
            {
                "entity_id": "input_text.evaluation_log_interpolated",
                "value": f"{hass.states.get('sensor.time').state}: Geen data beschikbaar (5m)",
            },
        )
    else:
        data_length = len(real_data)
        logger.info(f"Werkelijke data punten (5m): {data_length}")

        # Bereken huidige 5-minuten slot sinds middernacht
        # Dit komt overeen met hoeveel 5-minuten blokken er zijn verstreken vandaag
        # De interpolated sensoren hebben state = huidige slot index
        solcast_state = hass.states.get("sensor.solcast_interpolated_forecast")
        if solcast_state and solcast_state.state not in ["unavailable", "unknown"]:
            try:
                current_slot = int(solcast_state.state)
            except (ValueError, TypeError):
                # Fallback: gebruik lengte van real_data als proxy voor slot
                # (real_data bevat alle 5-min blokken vanaf middernacht tot nu)
                current_slot = data_length - 1 if data_length > 0 else 0
        else:
            # Fallback: gebruik lengte van real_data als proxy voor slot
            current_slot = data_length - 1 if data_length > 0 else 0

        logger.info(f"Huidige 5-minuten slot: {current_slot}")

        predictors = {
            "solcast": {
                "entity": "sensor.solcast_interpolated_forecast",
                "attribute": "five_minute_series",
                "display_name": "Solcast 5m",
            },
            "solcast10": {
                "entity": "sensor.solcast_interpolated_forecast",
                "attribute": "five_minute_series_p10",
                "display_name": "Solcast 10% 5m",
            },
            "solcast90": {
                "entity": "sensor.solcast_interpolated_forecast",
                "attribute": "five_minute_series_p90",
                "display_name": "Solcast 90% 5m",
            },
            "openmeteo": {
                "entity": "sensor.open_meteo_interpolated_forecast",
                "attribute": "five_minute_series",
                "display_name": "OpenMeteo 5m",
            },
        }

        results = {}

        for predictor_key, predictor_info in predictors.items():
            history_data = get_interpolated_series(
                predictor_info["entity"], predictor_info["attribute"], current_slot
            )

            if history_data:
                mse = calculate_mse(real_data, history_data)
                mae = calculate_mae(real_data, history_data)
                rmse = calculate_rmse(mse)
                mape = calculate_mape(real_data, history_data)

                results[predictor_key] = {
                    "mse": mse,
                    "mae": mae,
                    "rmse": rmse,
                    "mape": mape,
                    "display_name": predictor_info["display_name"],
                    "data_points": min(len(real_data), len(history_data)),
                }

                logger.info(
                    f"{predictor_info['display_name']}: "
                    f"MSE={mse:.2f}, MAE={mae:.2f}, RMSE={rmse:.2f}, MAPE={mape:.2f}%"
                )
            else:
                logger.warning(
                    f"Geen 5m lijst data voor {predictor_info['display_name']}"
                )
                results[predictor_key] = {
                    "mse": float("inf"),
                    "mae": float("inf"),
                    "rmse": float("inf"),
                    "mape": float("inf"),
                    "display_name": predictor_info["display_name"],
                    "data_points": 0,
                }

        entity_suffix = {
            "solcast": "solcast_interp",
            "solcast10": "solcast10_interp",
            "solcast90": "solcast90_interp",
            "openmeteo": "openmeteo_interp",
        }

        for predictor_key, metrics in results.items():
            suffix = entity_suffix[predictor_key]
            hass.services.call(
                "input_number",
                "set_value",
                {
                    "entity_id": f"input_number.{suffix}_mse",
                    "value": metrics["mse"] if metrics["mse"] != float("inf") else 999999,
                },
            )
            hass.services.call(
                "input_number",
                "set_value",
                {
                    "entity_id": f"input_number.{suffix}_mae",
                    "value": metrics["mae"] if metrics["mae"] != float("inf") else 999999,
                },
            )

        valid_results = {k: v for k, v in results.items() if v["mse"] != float("inf")}

        if valid_results:
            best_predictor_key = min(
                valid_results.keys(), key=lambda k: valid_results[k]["mse"]
            )
            best_predictor_name = valid_results[best_predictor_key]["display_name"]

            current_best = hass.states.get(
                "input_text.best_solar_predictor_interpolated"
            ).state

            if current_best != best_predictor_key:
                hass.services.call(
                    "input_text",
                    "set_value",
                    {
                        "entity_id": "input_text.best_solar_predictor_interpolated",
                        "value": best_predictor_key,
                    },
                )
                logger.info(f"Beste 5m voorspeller gewijzigd naar: {best_predictor_name}")
            else:
                logger.info(f"Beste 5m voorspeller blijft: {best_predictor_name}")

            log_evaluation_results(results, best_predictor_key)
        else:
            logger.error("Geen geldige 5m voorspelling data beschikbaar")
            hass.services.call(
                "input_text",
                "set_value",
                {
                    "entity_id": "input_text.evaluation_log_interpolated",
                    "value": f"{hass.states.get('sensor.time').state}: Geen geldige voorspellingen (5m)",
                },
            )

except Exception as e:
    logger.error(f"Fout in 5m solar evaluatie script: {str(e)}")
    hass.services.call(
        "input_text",
        "set_value",
        {
            "entity_id": "input_text.evaluation_log_interpolated",
            "value": f"{hass.states.get('sensor.time').state}: Script fout 5m - {str(e)[:50]}",
        },
    )
    hass.services.call(
        "persistent_notification",
        "create",
        {
            "message": f"Fout in 5m solar evaluatie script: {str(e)}",
            "title": "⚠️ Solar Evaluatie Fout (5m)",
            "notification_id": "solar_evaluation_error_5m",
        },
    )



####kak gvd