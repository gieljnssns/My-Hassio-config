"""Config flow for MQTT."""
from collections import OrderedDict
import logging
import queue

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PAYLOAD,
    CONF_PORT,
    CONF_PROTOCOL,
    CONF_USERNAME,
)

from .const import (
    ATTR_PAYLOAD,
    ATTR_QOS,
    ATTR_RETAIN,
    ATTR_TOPIC,
    CONF_BIRTH_MESSAGE,
    CONF_BROKER,
    CONF_DISCOVERY,
    CONF_WILL_MESSAGE,
    DATA_MQTT_CONFIG,
    DEFAULT_BIRTH,
    DEFAULT_DISCOVERY,
    DEFAULT_WILL,
)
from .util import MQTT_WILL_BIRTH_SCHEMA

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register("mqtt")
class FlowHandler(config_entries.ConfigFlow):
    """Handle a config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    _hassio_discovery = None

    @staticmethod
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return MQTTOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return await self.async_step_broker()

    async def async_step_broker(self, user_input=None):
        """Confirm the setup."""
        errors = {}

        if user_input is not None:
            can_connect = await self.hass.async_add_executor_job(
                try_connection,
                user_input[CONF_BROKER],
                user_input[CONF_PORT],
                user_input.get(CONF_USERNAME),
                user_input.get(CONF_PASSWORD),
            )

            if can_connect:
                return self.async_create_entry(
                    title=user_input[CONF_BROKER], data=user_input
                )

            errors["base"] = "cannot_connect"

        fields = OrderedDict()
        fields[vol.Required(CONF_BROKER)] = str
        fields[vol.Required(CONF_PORT, default=1883)] = vol.Coerce(int)
        fields[vol.Optional(CONF_USERNAME)] = str
        fields[vol.Optional(CONF_PASSWORD)] = str
        fields[vol.Optional(CONF_DISCOVERY, default=DEFAULT_DISCOVERY)] = bool

        return self.async_show_form(
            step_id="broker", data_schema=vol.Schema(fields), errors=errors
        )

    async def async_step_import(self, user_input):
        """Import a config entry.

        Special type of import, we're not actually going to store any data.
        Instead, we're going to rely on the values that are in config file.
        """
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(title="configuration.yaml", data={})

    async def async_step_hassio(self, discovery_info):
        """Receive a Hass.io discovery."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        self._hassio_discovery = discovery_info

        return await self.async_step_hassio_confirm()

    async def async_step_hassio_confirm(self, user_input=None):
        """Confirm a Hass.io discovery."""
        errors = {}

        if user_input is not None:
            data = self._hassio_discovery
            can_connect = await self.hass.async_add_executor_job(
                try_connection,
                data[CONF_HOST],
                data[CONF_PORT],
                data.get(CONF_USERNAME),
                data.get(CONF_PASSWORD),
                data.get(CONF_PROTOCOL),
            )

            if can_connect:
                return self.async_create_entry(
                    title=data["addon"],
                    data={
                        CONF_BROKER: data[CONF_HOST],
                        CONF_PORT: data[CONF_PORT],
                        CONF_USERNAME: data.get(CONF_USERNAME),
                        CONF_PASSWORD: data.get(CONF_PASSWORD),
                        CONF_PROTOCOL: data.get(CONF_PROTOCOL),
                        CONF_DISCOVERY: user_input[CONF_DISCOVERY],
                    },
                )

            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="hassio_confirm",
            description_placeholders={"addon": self._hassio_discovery["addon"]},
            data_schema=vol.Schema(
                {vol.Optional(CONF_DISCOVERY, default=DEFAULT_DISCOVERY): bool}
            ),
            errors=errors,
        )


class MQTTOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle MQTT options."""

    def __init__(self, config_entry):
        """Initialize MQTT options flow."""
        self.config_entry = config_entry
        self.broker_config = {}
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):
        """Manage the MQTT options."""
        return await self.async_step_broker()

    async def async_step_broker(self, user_input=None):
        """Manage the MQTT options."""
        errors = {}
        current_config = self.config_entry.data
        yaml_config = self.hass.data.get(DATA_MQTT_CONFIG, {})
        if user_input is not None:
            can_connect = await self.hass.async_add_executor_job(
                try_connection,
                user_input[CONF_BROKER],
                user_input[CONF_PORT],
                user_input.get(CONF_USERNAME),
                user_input.get(CONF_PASSWORD),
            )

            if can_connect:
                self.broker_config.update(user_input)
                return await self.async_step_options()

            errors["base"] = "cannot_connect"

        fields = OrderedDict()
        current_broker = current_config.get(CONF_BROKER, yaml_config.get(CONF_BROKER))
        current_port = current_config.get(CONF_PORT, yaml_config.get(CONF_PORT))
        current_user = current_config.get(CONF_USERNAME, yaml_config.get(CONF_USERNAME))
        current_pass = current_config.get(CONF_PASSWORD, yaml_config.get(CONF_PASSWORD))
        fields[vol.Required(CONF_BROKER, default=current_broker)] = str
        fields[vol.Required(CONF_PORT, default=current_port)] = vol.Coerce(int)
        fields[
            vol.Optional(
                CONF_USERNAME,
                description={"suggested_value": current_user},
            )
        ] = str
        fields[
            vol.Optional(
                CONF_PASSWORD,
                description={"suggested_value": current_pass},
            )
        ] = str

        return self.async_show_form(
            step_id="broker",
            data_schema=vol.Schema(fields),
            errors=errors,
        )

    async def async_step_options(self, user_input=None):
        """Manage the MQTT options."""
        errors = {}
        current_config = self.config_entry.data
        yaml_config = self.hass.data.get(DATA_MQTT_CONFIG, {})
        options_config = {}
        if user_input is not None:
            bad_birth = False
            bad_will = False

            if "birth_topic" in user_input:
                birth_message = {
                    ATTR_TOPIC: user_input["birth_topic"],
                    ATTR_PAYLOAD: user_input.get("birth_payload", ""),
                    ATTR_QOS: user_input["birth_qos"],
                    ATTR_RETAIN: user_input["birth_retain"],
                }
                try:
                    birth_message = MQTT_WILL_BIRTH_SCHEMA(birth_message)
                    options_config[CONF_BIRTH_MESSAGE] = birth_message
                except vol.Invalid:
                    errors["base"] = "bad_birth"
                    bad_birth = True
            if not user_input["birth_enable"]:
                options_config[CONF_BIRTH_MESSAGE] = {}

            if "will_topic" in user_input:
                will_message = {
                    ATTR_TOPIC: user_input["will_topic"],
                    ATTR_PAYLOAD: user_input.get("will_payload", ""),
                    ATTR_QOS: user_input["will_qos"],
                    ATTR_RETAIN: user_input["will_retain"],
                }
                try:
                    will_message = MQTT_WILL_BIRTH_SCHEMA(will_message)
                    options_config[CONF_WILL_MESSAGE] = will_message
                except vol.Invalid:
                    errors["base"] = "bad_will"
                    bad_will = True
            if not user_input["will_enable"]:
                options_config[CONF_WILL_MESSAGE] = {}

            options_config[CONF_DISCOVERY] = user_input[CONF_DISCOVERY]

            if not bad_birth and not bad_will:
                updated_config = {}
                updated_config.update(self.broker_config)
                updated_config.update(options_config)
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=updated_config
                )
                return self.async_create_entry(title="", data=None)

        birth = {
            **DEFAULT_BIRTH,
            **current_config.get(
                CONF_BIRTH_MESSAGE, yaml_config.get(CONF_BIRTH_MESSAGE, {})
            ),
        }
        will = {
            **DEFAULT_WILL,
            **current_config.get(
                CONF_WILL_MESSAGE, yaml_config.get(CONF_WILL_MESSAGE, {})
            ),
        }
        discovery = current_config.get(
            CONF_DISCOVERY, yaml_config.get(CONF_DISCOVERY, DEFAULT_DISCOVERY)
        )

        fields = OrderedDict()
        fields[vol.Optional(CONF_DISCOVERY, default=discovery)] = bool

        # Birth message is disabled if CONF_BIRTH_MESSAGE = {}
        fields[
            vol.Optional(
                "birth_enable",
                default=CONF_BIRTH_MESSAGE not in current_config
                or current_config[CONF_BIRTH_MESSAGE] != {},
            )
        ] = bool
        fields[
            vol.Optional(
                "birth_topic", description={"suggested_value": birth[ATTR_TOPIC]}
            )
        ] = str
        fields[
            vol.Optional(
                "birth_payload", description={"suggested_value": birth[CONF_PAYLOAD]}
            )
        ] = str
        fields[vol.Optional("birth_qos", default=birth[ATTR_QOS])] = vol.In([0, 1, 2])
        fields[vol.Optional("birth_retain", default=birth[ATTR_RETAIN])] = bool

        # Will message is disabled if CONF_WILL_MESSAGE = {}
        fields[
            vol.Optional(
                "will_enable",
                default=CONF_WILL_MESSAGE not in current_config
                or current_config[CONF_WILL_MESSAGE] != {},
            )
        ] = bool
        fields[
            vol.Optional(
                "will_topic", description={"suggested_value": will[ATTR_TOPIC]}
            )
        ] = str
        fields[
            vol.Optional(
                "will_payload", description={"suggested_value": will[CONF_PAYLOAD]}
            )
        ] = str
        fields[vol.Optional("will_qos", default=will[ATTR_QOS])] = vol.In([0, 1, 2])
        fields[vol.Optional("will_retain", default=will[ATTR_RETAIN])] = bool

        return self.async_show_form(
            step_id="options",
            data_schema=vol.Schema(fields),
            errors=errors,
        )


def try_connection(broker, port, username, password, protocol="3.1"):
    """Test if we can connect to an MQTT broker."""
    # pylint: disable=import-outside-toplevel
    import paho.mqtt.client as mqtt

    if protocol == "3.1":
        proto = mqtt.MQTTv31
    else:
        proto = mqtt.MQTTv311

    client = mqtt.Client(protocol=proto)
    if username and password:
        client.username_pw_set(username, password)

    result = queue.Queue(maxsize=1)

    def on_connect(client_, userdata, flags, result_code):
        """Handle connection result."""
        result.put(result_code == mqtt.CONNACK_ACCEPTED)

    client.on_connect = on_connect

    client.connect_async(broker, port)
    client.loop_start()

    try:
        return result.get(timeout=5)
    except queue.Empty:
        return False
    finally:
        client.disconnect()
        client.loop_stop()
