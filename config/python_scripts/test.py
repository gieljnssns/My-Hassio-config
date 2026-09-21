"""
Solar evaluation script for interpolated 5-minute forecasts.
Calculates MSE, MAE, RMSE, MAPE and cumulative energy (kWh) for
Solcast/OpenMeteo/ML interpolated series.

Uitlijning gebeurt op basis van het 5-minuten-slot sinds middernacht (0-287),
afgeleid uit de start-timestamp van elke recorder-statistic-entry, in plaats
van positionele indexering. Dit voorkomt scheve vergelijkingen wanneer de
recorder een gat heeft (bv. door een tijdelijk unavailable sensor).
"""


def get_slot_index(timestamp_value):
    """Bepaal het 5-minuten-slot (0-287) sinds lokale middernacht uit een timestamp."""
    try:
        if isinstance(timestamp_value, str):
            ts = timestamp_value.replace("Z", "+00:00")
            dt = datetime.datetime.fromisoformat(ts)
        else:
            dt = timestamp_value

        if dt.tzinfo is not None:
            dt = dt.astimezone()

        minutes_since_midnight = dt.hour * 60 + dt.minute
        return minutes_since_midnight // 5
    except (ValueError, TypeError, AttributeError):
        return None


def calculate_mse(actual, predicted):
    if not actual or not predicted:
        return float("inf")
    min_length = min(len(actual), len(predicted))
    if min_length == 0:
        return float("inf")
    actual_slice = actual[:min_length]
    predicted_slice = predicted[:min_length]
    return sum((a - p) ** 2 for a, p in zip(actual_slice, predicted_slice)) / min_length


def calculate_mae(actual, predicted):
    if not actual or not predicted:
        return float("inf")
    min_length = min(len(actual), len(predicted))
    if min_length == 0:
        return float("inf")
    actual_slice = actual[:min_length]
    predicted_slice = predicted[:min_length]
    return sum(abs(a - p) for a, p in zip(actual_slice, predicted_slice)) / min_length


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
    return sum(abs((a - p) / a) for a, p in valid_pairs) / len(valid_pairs) * 100


def calculate_energy_kwh(power_values, interval_minutes=5):
    """Integreer een lijst vermogenswaarden (W) over 5-minuten-sloten naar energie (kWh)."""
    if not power_values:
        return 0.0
    interval_hours = interval_minutes / 60
    return sum(power_values) * interval_hours / 1000


def extract_statistics_by_slot(statistics_data):
    """Geef een dict {slot_index: mean} terug, op basis van de start-timestamp
    van elke entry. Ontbrekende slots (recorder-gaten) komen simpelweg niet voor
    in de dict, in plaats van de reeks positioneel te verschuiven."""
    try:
        stats_root = statistics_data.get("statistics", statistics_data)
        sensor_stats = stats_root.get("sensor.huidige_opbrengst_gefilterd", [])
    except (AttributeError, TypeError, KeyError):
        logger.warning("Kon statistics data niet parsen")
        return {}

    by_slot = {}
    for entry in sensor_stats:
        mean_value = entry.get("mean")
        if mean_value is None:
            continue
        slot = get_slot_index(entry.get("start"))
        if slot is None:
            continue
        by_slot[slot] = mean_value

    return by_slot


def get_interpolated_series(entity_id, attribute_name):
    """Haal de volledige dag-reeks (slot 0 = 00:00) op van een attribuut."""
    try:
        entity_state = hass.states.get(entity_id)
        if not entity_state or not entity_state.attributes:
            return []
        raw = entity_state.attributes.get(attribute_name, [])
        if not raw:
            return []
        return [float(x) for x in raw if x is not None]
    except (ValueError, TypeError):
        logger.warning(f"Kon {attribute_name} data niet ophalen van {entity_id}")
        return []


def build_aligned_pairs(real_by_slot, predicted_series, max_slot):
    """Koppel werkelijke en voorspelde waarden per slot, zodat recorder-gaten
    of ontbrekende voorspelde punten geen verschuiving veroorzaken."""
    actual = []
    predicted = []
    for slot in sorted(real_by_slot.keys()):
        if slot > max_slot:
            continue
        if slot < len(predicted_series):
            actual.append(real_by_slot[slot])
            predicted.append(predicted_series[slot])
    return actual, predicted


def log_evaluation_results(results, best_predictor):
    current_time = hass.states.get("sensor.time").state
    best = results[best_predictor]
    log_message = (
        f"{current_time}: {best_predictor} (5m MSE: {best['mse']:.2f}, "
        f"Energie: {best['energy_actual_kwh']:.2f} kWh werkelijk vs "
        f"{best['energy_predicted_kwh']:.2f} kWh voorspeld, "
        f"Δ {best['energy_error_kwh']:+.2f} kWh)"
    )

    hass.services.call(
        "input_text",
        "set_value",
        {"entity_id": "input_text.evaluation_log_interpolated", "value": log_message},
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
    real_by_slot = extract_statistics_by_slot(statistics_data)

    if not real_by_slot:
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
        logger.info(f"Werkelijke data punten (5m): {len(real_by_slot)}")

        current_slot = get_slot_index(current_time_str)
        if current_slot is None:
            current_slot = max(real_by_slot.keys())
            logger.warning(
                f"Kon huidige slot niet uit current_time afleiden, fallback naar {current_slot}"
            )

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
            "ml": {
                "entity": "sensor.ml_interpolated_forecast",
                "attribute": "five_minute_series",
                "display_name": "Ml 5m",
            },
        }

        results = {}

        for predictor_key, predictor_info in predictors.items():
            predicted_series = get_interpolated_series(
                predictor_info["entity"], predictor_info["attribute"]
            )
            actual_aligned, predicted_aligned = build_aligned_pairs(
                real_by_slot, predicted_series, current_slot
            )

            if actual_aligned:
                mse = calculate_mse(actual_aligned, predicted_aligned)
                mae = calculate_mae(actual_aligned, predicted_aligned)
                rmse = calculate_rmse(mse)
                mape = calculate_mape(actual_aligned, predicted_aligned)

                energy_actual_kwh = calculate_energy_kwh(actual_aligned)
                energy_predicted_kwh = calculate_energy_kwh(predicted_aligned)
                energy_error_kwh = energy_actual_kwh - energy_predicted_kwh
                energy_ape = (
                    abs(energy_error_kwh) / energy_actual_kwh * 100
                    if energy_actual_kwh != 0
                    else float("inf")
                )

                results[predictor_key] = {
                    "mse": mse,
                    "mae": mae,
                    "rmse": rmse,
                    "mape": mape,
                    "energy_actual_kwh": energy_actual_kwh,
                    "energy_predicted_kwh": energy_predicted_kwh,
                    "energy_error_kwh": energy_error_kwh,
                    "energy_ape": energy_ape,
                    "display_name": predictor_info["display_name"],
                    "data_points": len(actual_aligned),
                }

                logger.info(
                    f"{predictor_info['display_name']}: "
                    f"MSE={mse:.2f}, MAE={mae:.2f}, RMSE={rmse:.2f}, MAPE={mape:.2f}%, "
                    f"Energie={energy_actual_kwh:.2f}/{energy_predicted_kwh:.2f} kWh "
                    f"(Δ {energy_error_kwh:+.2f} kWh, {energy_ape:.1f}%)"
                )
            else:
                logger.warning(
                    f"Geen overlappende 5m data voor {predictor_info['display_name']}"
                )
                results[predictor_key] = {
                    "mse": float("inf"),
                    "mae": float("inf"),
                    "rmse": float("inf"),
                    "mape": float("inf"),
                    "energy_actual_kwh": 0.0,
                    "energy_predicted_kwh": 0.0,
                    "energy_error_kwh": 0.0,
                    "energy_ape": float("inf"),
                    "display_name": predictor_info["display_name"],
                    "data_points": 0,
                }

        entity_suffix = {
            "solcast": "solcast_interp",
            "solcast10": "solcast10_interp",
            "solcast90": "solcast90_interp",
            "openmeteo": "openmeteo_interp",
            "ml": "ml_interp",
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
            hass.services.call(
                "input_number",
                "set_value",
                {
                    "entity_id": f"input_number.{suffix}_energy_actual_kwh",
                    "value": metrics["energy_actual_kwh"],
                },
            )
            hass.services.call(
                "input_number",
                "set_value",
                {
                    "entity_id": f"input_number.{suffix}_energy_predicted_kwh",
                    "value": metrics["energy_predicted_kwh"],
                },
            )
            hass.services.call(
                "input_number",
                "set_value",
                {
                    "entity_id": f"input_number.{suffix}_energy_error_kwh",
                    "value": metrics["energy_error_kwh"],
                },
            )
            hass.services.call(
                "input_number",
                "set_value",
                {
                    "entity_id": f"input_number.{suffix}_energy_ape",
                    "value": metrics["energy_ape"] if metrics["energy_ape"] != float("inf") else 999999,
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