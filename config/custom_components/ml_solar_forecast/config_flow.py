"""Configuration flow for the HA-ML Solar Forecast integration."""

import voluptuous as vol
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    EntityFilterSelectorConfig,
    EntitySelector,
    EntitySelectorConfig,
    LocationSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_APP_HOSTNAME,
    CONF_INFLUX_DB,
    CONF_INFLUX_ENTITY,
    CONF_INFLUX_HOST,
    CONF_INFLUX_PASS,
    CONF_INFLUX_PORT,
    CONF_INFLUX_USER,
    CONF_LOCATION,
    CONF_MAX_INVERTER_POWER_W,
    CONF_OPENMETEO_API_KEY,
    CONF_OPENMETEO_WEATHER_MODELS,
    CONF_PRODUCTION_ENTITY,
    CONF_TRAINING_DAYS,
    CONF_USE_INFLUX,
    DEFAULT_APP_HOSTNAME,
    DEFAULT_INFLUX_HOST,
    DOMAIN,
    MIN_TRAINING_DAYS,
    log,
)
from .lgbm import LGBM


class MLSolarForecastConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for ML Solar Forecast integration."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the ML Solar Forecast config flow."""
        self.config_data: dict[str, any] = {}

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Store all input for validation
            self.config_data.update(user_input)

            # Validate location first
            if CONF_LOCATION not in user_input or not user_input[CONF_LOCATION]:
                errors["base"] = "location_required"
            else:
                # Validate training days
                if user_input.get(CONF_TRAINING_DAYS, 0) < MIN_TRAINING_DAYS:
                    errors["base"] = "training_days_too_low"

                # Validate max inverter power
                if (
                    CONF_MAX_INVERTER_POWER_W in user_input
                    and user_input[CONF_MAX_INVERTER_POWER_W] is not None
                ):
                    if (
                        user_input[CONF_MAX_INVERTER_POWER_W] < 100
                        or user_input[CONF_MAX_INVERTER_POWER_W] > 100000
                    ):
                        errors["base"] = "max_inverter_power_invalid"

                # Validate OpenMeteo API key if provided
                if (
                    CONF_OPENMETEO_API_KEY in user_input
                    and user_input[CONF_OPENMETEO_API_KEY]
                ):
                    # Just check if it's not empty (basic validation)
                    pass

                # Validate OpenMeteo weather models if provided
                if (
                    CONF_OPENMETEO_WEATHER_MODELS in user_input
                    and user_input[CONF_OPENMETEO_WEATHER_MODELS]
                ):
                    # Just check if it's not empty (basic validation)
                    pass

                # Validate app hostname
                app_hostname = user_input.get(CONF_APP_HOSTNAME, DEFAULT_APP_HOSTNAME)
                if not app_hostname:
                    errors["base"] = "app_hostname_required"
                else:
                    try:
                        lgbm = LGBM("connection_test", app_hostname)
                        await lgbm.is_trained()
                    except Exception as e:
                        errors["base"] = "cannot_connect_app"
                        log.error("Failed to connect to app at %s: %s", app_hostname, e)

            # If no errors so far, proceed to next step based on use_influx
            if not errors:
                # If use_influx is True, go to influx config step
                if user_input.get(CONF_USE_INFLUX, False):
                    return await self.async_step_influx_config()
                else:
                    # Otherwise, proceed to production entity step
                    return await self.async_step_production_entity()

        # Show initial configuration form with location first
        return self.async_show_form(
            step_id="user",
            data_schema=self._get_initial_schema(user_input),
            errors=errors,
            description_placeholders={
                "min_training_days": str(MIN_TRAINING_DAYS),
            },
        )

    async def async_step_influx_config(self, user_input=None) -> FlowResult:
        """Handle InfluxDB configuration step."""
        errors = {}

        if user_input is not None:
            # Store all input for validation
            self.config_data.update(user_input)

            # Validate influx entity
            influx_entity = user_input.get(CONF_INFLUX_ENTITY)
            if not influx_entity:
                errors["base"] = "entity_required"
                log.warning("Influx entity must be provided")

            # Validate InfluxDB host if provided
            if not errors:
                influx_host = user_input.get(CONF_INFLUX_HOST, "")
                if not influx_host:
                    errors["base"] = "influx_host_required"
                    log.warning("InfluxDB host is required when using Influx")
                else:
                    # Normalize host by removing protocol if present
                    influx_host = influx_host.strip()
                    if "://" in influx_host:
                        influx_host = influx_host.split("://")[-1]
                    # Remove any path or query parameters
                    if "/" in influx_host:
                        influx_host = influx_host.split("/")[0]
                    # Remove any port specification if present
                    if ":" in influx_host:
                        host_parts = influx_host.split(":")
                        influx_host = host_parts[0]
                        # If this is a host:port format, extract the port
                        if len(host_parts) > 1:
                            try:
                                port_num = int(host_parts[1])
                                if (
                                    CONF_INFLUX_PORT not in user_input
                                    or not user_input.get(CONF_INFLUX_PORT)
                                ):
                                    user_input[CONF_INFLUX_PORT] = port_num
                            except ValueError:
                                pass

                    user_input[CONF_INFLUX_HOST] = influx_host
                    log.debug("Normalized InfluxDB host: %s", influx_host)

            # Create entry if no errors
            if not errors:
                return self.async_create_entry(
                    title=self._get_title(), data=self.config_data
                )

        # Show influx config form
        return self.async_show_form(
            step_id="influx_config",
            data_schema=self._get_influx_schema(user_input),
            errors=errors,
        )

    async def async_step_production_entity(self, user_input=None) -> FlowResult:
        """Handle production entity configuration step."""
        errors = {}

        if user_input is not None:
            # Store all input for validation
            self.config_data.update(user_input)

            # Validate production entity
            production_entity = user_input.get(CONF_PRODUCTION_ENTITY)
            if not production_entity:
                errors["base"] = "entity_required"
                log.warning("Production entity must be provided")
            elif production_entity and not self.hass.states.get(production_entity):
                errors["base"] = "entity_not_found"
                log.warning("Production entity %s not found", production_entity)

            # Create entry if no errors
            if not errors:
                return self.async_create_entry(
                    title=self._get_title(), data=self.config_data
                )

        # Show production entity form
        return self.async_show_form(
            step_id="production_entity",
            data_schema=self._get_production_schema(user_input),
            errors=errors,
        )

    def _get_title(self) -> str:
        """Generate a title for the config entry."""
        # Generate unique title based on entity
        if (
            CONF_INFLUX_ENTITY in self.config_data
            and self.config_data[CONF_INFLUX_ENTITY]
        ):
            entity_id = self.config_data[CONF_INFLUX_ENTITY]
        elif (
            CONF_PRODUCTION_ENTITY in self.config_data
            and self.config_data[CONF_PRODUCTION_ENTITY]
        ):
            entity_id = self.config_data[CONF_PRODUCTION_ENTITY]
        else:
            entity_id = "Unknown"

        return f"Solar Forecast ({entity_id.split('.')[-1]})"

    def _get_initial_schema(self, user_input: dict | None = None) -> vol.Schema:
        """Get the initial configuration schema."""
        if user_input is None:
            user_input = {}

        return vol.Schema(
            {
                vol.Required(
                    CONF_LOCATION,
                    default=user_input.get(
                        CONF_LOCATION,
                        {
                            "latitude": self.hass.config.latitude,
                            "longitude": self.hass.config.longitude,
                        },
                    ),
                ): LocationSelector({"radius": False}),
                vol.Required(
                    CONF_TRAINING_DAYS,
                    default=user_input.get(CONF_TRAINING_DAYS),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_TRAINING_DAYS,
                        max=730,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="days",
                    )
                ),
                vol.Optional(
                    CONF_MAX_INVERTER_POWER_W,
                    **(
                        {"default": user_input[CONF_MAX_INVERTER_POWER_W]}
                        if CONF_MAX_INVERTER_POWER_W in user_input
                        else {}
                    ),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=100,
                        max=100000,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="W",
                    )
                ),
                vol.Optional(
                    CONF_OPENMETEO_API_KEY,
                    default=user_input.get(CONF_OPENMETEO_API_KEY, ""),
                ): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
                vol.Optional(
                    CONF_OPENMETEO_WEATHER_MODELS,
                    default=user_input.get(CONF_OPENMETEO_WEATHER_MODELS, ""),
                ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
                vol.Optional(
                    CONF_APP_HOSTNAME,
                    default=user_input.get(CONF_APP_HOSTNAME, DEFAULT_APP_HOSTNAME),
                ): TextSelector(
                    TextSelectorConfig(
                        type=TextSelectorType.URL,
                    )
                ),
                vol.Optional(
                    CONF_USE_INFLUX,
                    default=user_input.get(CONF_USE_INFLUX, False),
                ): bool,
            }
        )

    def _get_influx_schema(self, user_input: dict | None = None) -> vol.Schema:
        """Get the InfluxDB configuration schema."""
        if user_input is None:
            user_input = {}

        return vol.Schema(
            {
                vol.Required(
                    CONF_INFLUX_ENTITY,
                    default=user_input.get(CONF_INFLUX_ENTITY),
                ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
                vol.Optional(
                    CONF_INFLUX_HOST,
                    default=user_input.get(CONF_INFLUX_HOST, DEFAULT_INFLUX_HOST),
                ): TextSelector(
                    TextSelectorConfig(
                        type=TextSelectorType.URL,
                    )
                ),
                vol.Optional(
                    CONF_INFLUX_PORT,
                    default=user_input.get(CONF_INFLUX_PORT, 8086),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1,
                        max=65535,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="port",
                    )
                ),
                vol.Optional(
                    CONF_INFLUX_USER,
                    default=user_input.get(CONF_INFLUX_USER, ""),
                ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
                vol.Optional(
                    CONF_INFLUX_PASS,
                    default=user_input.get(CONF_INFLUX_PASS, ""),
                ): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
                vol.Optional(
                    CONF_INFLUX_DB,
                    default=user_input.get(CONF_INFLUX_DB, ""),
                ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
            }
        )

    def _get_production_schema(self, user_input: dict | None = None) -> vol.Schema:
        """Get the production entity configuration schema."""
        if user_input is None:
            user_input = {}

        return vol.Schema(
            {
                vol.Required(
                    CONF_PRODUCTION_ENTITY,
                    default=user_input.get(CONF_PRODUCTION_ENTITY, ""),
                ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
            }
        )
