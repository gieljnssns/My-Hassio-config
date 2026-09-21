"""
Solar evaluation script for interpolated 5-minute forecasts.
Selecteert de beste voorspeller op basis van een gewogen combinatie van
genormaliseerde MAE (vermogensprofiel) en energie-APE (dagbudget).
"""


def get_slot_index(timestamp_value):
    try:
        if isinstance(timestamp_value, str):
            ts = timestamp_value.replace("Z", "+00:00")
            dt = datetime.datetime.fromisoformat(ts)
        else:
            dt = timestamp_value
        if dt.tzinfo is not None:
            dt = dt.astimezone()
        return (dt.hour * 60 + dt.minute) // 5
    except (ValueError, TypeError, AttributeError):
        return None


def calculate_mae(actual, predicted):
    if not actual or not predicted:
        return float("inf")
    n = min(len(actual), len(predicted))
    return sum(abs(a - p) for a, p in zip(actual[:n], predicted[:n])) / n


def calculate_energy_kwh(power_values, interval_minutes=5):
    if not power_values:
        return 0.0
    return sum(power_values) * (interval_minutes / 60) / 1000


def calculate_combined_score(
    mae, actual_aligned, energy_error_kwh, energy_actual_kwh, w_mae=0.6, w_energy=0.4
):
    """
    Gecombineerde score (lager = beter) als gewogen gemiddelde van:
      - MAE als % van het gemiddeld actueel vermogen  (shape-nauwkeurigheid)
      - |energie-fout| als % van werkelijke energie   (dagbudget-nauwkeurigheid)
    Beide in % zodat ze op dezelfde schaal staan.
    Gewichten: w_mae + w_energy = 1.0 — verhoog w_energy als dagbudget
    zwaarder moet wegen dan het momentane vermogensprofiel.
    """
    if mae == float("inf"):
        return float("inf")

    mean_actual = sum(actual_aligned) / len(actual_aligned) if actual_aligned else 0
    mae_pct = (mae / mean_actual * 100) if mean_actual > 0 else float("inf")
    energy_ape = (
        (abs(energy_error_kwh) / energy_actual_kwh * 100)
        if energy_actual_kwh > 0
        else float("inf")
    )

    if float("inf") in (mae_pct, energy_ape):
        return float("inf")

    return w_mae * mae_pct + w_energy * energy_ape


def extract_statistics_by_slot(statistics_data):
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
    try:
        entity_state = hass.states.get(entity_id)
        if not entity_state or not entity_state.attributes:
            return []
        raw = entity_state.attributes.get(attribute_name, [])
        if not raw:
            return []
        return [float(x) for x in raw if x is not None]
    except (ValueError, TypeError):
        logger.warning(f"Kon {attribute_name} niet ophalen van {entity_id}")
        return []


def build_aligned_pairs(real_by_slot, predicted_series, max_slot):
    actual, predicted = [], []
    for slot in sorted(real_by_slot.keys()):
        if slot > max_slot:
            continue
        if slot < len(predicted_series):
            actual.append(real_by_slot[slot])
            predicted.append(predicted_series[slot])
    return actual, predicted


# def log_evaluation_results(results, best_key, energy_actual_kwh):
#     best = results[best_key]
#     current_time = hass.states.get("sensor.time").state
#     log_message = (
#         f"{current_time}: {best['display_name']} "
#         f"(score={best['combined_score']:.1f}%, "
#         f"MAE={best['mae']:.0f}W, "
#         f"ΔE={best['energy_error_kwh']:+.3f} kWh van {energy_actual_kwh:.2f} kWh)"
#     )
#     hass.services.call(
#         "input_text", "set_value",
#         {"entity_id": "input_text.evaluation_log_interpolated", "value": log_message},
#     )
#     hass.services.call(
#         "input_datetime", "set_datetime",
#         {
#             "entity_id": "input_datetime.last_evaluation_time_interpolated",
#             "datetime": hass.states.get("sensor.date_time_iso").state,
#         },
#     )


try:
    statistics_data = data.get("statistics_data", {})
    current_time_str = data.get(
        "current_time", hass.states.get("sensor.date_time_iso").state
    )

    logger.info(f"Starting interpolated solar evaluation at {current_time_str}")
    real_by_slot = extract_statistics_by_slot(statistics_data)

    if not real_by_slot:
        logger.error("Geen werkelijke statistics data beschikbaar")
        hass.services.call(
            "input_text",
            "set_value",
            {
                "entity_id": "input_text.evaluation_log_interpolated",
                "value": f"{hass.states.get('sensor.time').state}: Geen data beschikbaar (5m)",
            },
        )
    else:
        logger.info(f"Werkelijke data punten: {len(real_by_slot)}")

        current_slot = get_slot_index(current_time_str)
        if current_slot is None:
            current_slot = max(real_by_slot.keys())
            logger.warning(
                f"Slot uit current_time niet bepaalbaar, fallback naar {current_slot}"
            )

        all_actual = [
            real_by_slot[s] for s in sorted(real_by_slot.keys()) if s <= current_slot
        ]
        energy_actual_kwh = calculate_energy_kwh(all_actual)
        logger.info(f"Werkelijke energie tot nu: {energy_actual_kwh:.3f} kWh")

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
                mae = calculate_mae(actual_aligned, predicted_aligned)
                energy_predicted = calculate_energy_kwh(predicted_aligned)
                energy_error = calculate_energy_kwh(actual_aligned) - energy_predicted
                score = calculate_combined_score(
                    mae, actual_aligned, energy_error, energy_actual_kwh
                )

                results[predictor_key] = {
                    "mae": mae,
                    "energy_error_kwh": energy_error,
                    "combined_score": score,
                    "display_name": predictor_info["display_name"],
                    "data_points": len(actual_aligned),
                }

                logger.info(
                    f"{predictor_info['display_name']}: "
                    f"score={score:.1f}%, MAE={mae:.0f}W, ΔE={energy_error:+.3f} kWh"
                )
            else:
                logger.warning(f"Geen data voor {predictor_info['display_name']}")
                results[predictor_key] = {
                    "mae": float("inf"),
                    "energy_error_kwh": 0.0,
                    "combined_score": float("inf"),
                    "display_name": predictor_info["display_name"],
                    "data_points": 0,
                }

        valid_results = {
            k: v for k, v in results.items() if v["combined_score"] != float("inf")
        }

        if valid_results:
            best_key = min(
                valid_results, key=lambda k: valid_results[k]["combined_score"]
            )
            best_name = valid_results[best_key]["display_name"]

            current_best = hass.states.get(
                "input_text.best_solar_predictor_interpolated"
            ).state

            if current_best != best_key:
                hass.services.call(
                    "input_text",
                    "set_value",
                    {
                        "entity_id": "input_text.best_solar_predictor_interpolated",
                        "value": best_key,
                    },
                )
                logger.info(f"Beste voorspeller gewijzigd naar: {best_name}")
            else:
                logger.info(f"Beste voorspeller blijft: {best_name}")

            # log_evaluation_results(results, best_key, energy_actual_kwh)
        else:
            logger.error("Geen geldige voorspelling data beschikbaar")
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
