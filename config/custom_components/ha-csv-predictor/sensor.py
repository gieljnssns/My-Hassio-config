"""Sensor platform for HA CSV Predictor."""
import logging

import numpy as np
import voluptuous as vol
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_CSV_PATH,
    CONF_DEPENDENT_VARIABLE,
    CONF_INDEPENDENT_VARIABLES,
    CONF_NEW_VARIABLES,
    ICON,
    SERVICE_PREDICT,
)
from .entity import HaCsvPredictorEntity
from .predictor import ModelTrainer

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup sensor platform."""
    # print("sensor async_setup_entry")
    # name = config_entry.data[CONF_NAME]
    csv_path = config_entry.data[CONF_CSV_PATH]
    # independent_variables = config_entry.data[CONF_INDEPENDENT_VARIABLES]
    # dependent_variable = config_entry.data[CONF_DEPENDENT_VARIABLE]
    # print(hass.config.path(csv_path))
    platform = entity_platform.async_get_current_platform()
    independent_variables = config_entry.data[CONF_INDEPENDENT_VARIABLES]
    # print(independent_variables)
    # print(type(independent_variables))
    # service_schema = vol.Schema()
    platform.async_register_entity_service(
        SERVICE_PREDICT,
        {vol.Required(CONF_NEW_VARIABLES): cv.ensure_list_csv},  # type: ignore
        "predict",
    )
    # platform.async_register_entity_service(
    #     SERVICE_PREDICT,
    #     {vol.Required(CONF_NEW_VARIABLES): cv.ensure_list_csv},  # type: ignore
    #     "predict",
    # )
    # coordinator = hass.data[DOMAIN][entry.entry_id]
    # model = PredictionModel()
    trainer = ModelTrainer(csv_path)
    # predictor = Predictor(model)

    async_add_entities(
        [
            HaCsvPredictorSensor(
                config_entry,
                # model,
                trainer,
                # predictor,
                # independent_variables,
                # dependent_variable,
            )
        ]
    )


class HaCsvPredictorSensor(HaCsvPredictorEntity, SensorEntity):
    """ha_csv_predictor Sensor class."""

    def __init__(
        self,
        config_entry,
        # model,
        trainer,
        # predictor,
        # independent_variables,
        # dependent_variable,
    ):
        """Initialize AdGuard Home sensor."""
        super().__init__(config_entry)
        # print("sensor HaCsvPredictorSensor")
        self._name = config_entry.data[CONF_NAME]
        # self._model = model
        self._trainer = trainer
        self._state = None
        # self._predictor = predictor
        self._independent_variables = config_entry.data[CONF_INDEPENDENT_VARIABLES]
        self._independent_variables_reverse = config_entry.data[
            CONF_INDEPENDENT_VARIABLES
        ].sort(reverse=True)
        self._dependent_variable = config_entry.data[CONF_DEPENDENT_VARIABLE]
        # print(self._independent_variables)
        # print(self._independent_variables_reverse)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON

    # @property
    # def device_class(self):
    #     """Return de device class of the sensor."""
    #     return "ha_csv_predictor__custom_device_class"

    async def predict(self, new_variables: dict) -> None:
        _LOGGER.debug(
            "%s: Increasing energy sensor with %s", self.entity_id, new_variables
        )
        data = await self._trainer.load_data()
        # print(data)
        X, y = await self._trainer.prepare_data(
            data, self._independent_variables, self._dependent_variable
        )
        # print("X", X)
        # print("y", y)
        await self._trainer.train(X, y)
        # print("new_variables", new_variables)

        variables = np.array([new_variables])
        # print("variables", variables)

        predicted = await self._trainer.predict(variables)

        # print(predicted)

        self._state = round(predicted[0][0], 2)
        # print(predicted[0])
        self.async_write_ha_state()
