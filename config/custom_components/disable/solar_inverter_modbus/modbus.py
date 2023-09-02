"""Support for Modbus."""
from time import sleep
import logging
import threading
from collections import OrderedDict

from pymodbus.client.sync import ModbusTcpClient

from homeassistant.const import (
    CONF_ADDRESS,
    CONF_DELAY,
    CONF_DEVICE_CLASS,
    CONF_HOST,
    CONF_NAME,
    CONF_OFFSET,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SLAVE,
    CONF_TIMEOUT,
    CONF_MONITORED_CONDITIONS,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_TYPE,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.helpers.discovery import load_platform

from .const import (
    CONF_BRAND,
    CONF_COUNT,
    CONF_DATA_TYPE,
    CONF_INPUT_TYPE,
    CONF_PRECISION,
    CONF_REVERSE_ORDER,
    CONF_SCALE,
    CONF_SENSOR,
    CONF_SENSORS,
    SOLAR_INVERTER_MODBUS_DOMAIN as DOMAIN,
)

from .huawei_const import HUAWEI_SENSORS

from .solaredge_const import SOLAREDGE_SENSORS

_LOGGER = logging.getLogger(__name__)


def modbus_setup(
    hass,
    config,
):  # sourcery no-metrics
    """Set up Modbus component."""
    _LOGGER.debug("Setup Modbus")
    hass.data[DOMAIN] = hub_collect = {}

    for conf_hub in config[DOMAIN]:
        if "monitored_conditions" in conf_hub:
            if "sensors" not in conf_hub:
                conf_hub[CONF_SENSORS] = [OrderedDict()]

            i = 0
            while i < (len(conf_hub[CONF_MONITORED_CONDITIONS]) - 2):
                for entry in conf_hub[CONF_MONITORED_CONDITIONS]:
                    if i < (len(conf_hub[CONF_MONITORED_CONDITIONS]) - 1):
                        conf_hub[CONF_SENSORS].append(OrderedDict())
                    if conf_hub[CONF_BRAND] == "huawei":
                        conf_hub[CONF_SENSORS][i][CONF_NAME] = HUAWEI_SENSORS[entry][0]
                        conf_hub[CONF_SENSORS][i][CONF_DATA_TYPE] = HUAWEI_SENSORS[
                            entry
                        ][1]
                        conf_hub[CONF_SENSORS][i][
                            CONF_UNIT_OF_MEASUREMENT
                        ] = HUAWEI_SENSORS[entry][2]
                        conf_hub[CONF_SENSORS][i][CONF_ADDRESS] = HUAWEI_SENSORS[entry][
                            4
                        ]
                        conf_hub[CONF_SENSORS][i][CONF_COUNT] = HUAWEI_SENSORS[entry][5]
                        conf_hub[CONF_SENSORS][i][CONF_DEVICE_CLASS] = HUAWEI_SENSORS[
                            entry
                        ][6]
                        conf_hub[CONF_SENSORS][i][CONF_INPUT_TYPE] = HUAWEI_SENSORS[
                            entry
                        ][7]
                        conf_hub[CONF_SENSORS][i][CONF_REVERSE_ORDER] = HUAWEI_SENSORS[
                            entry
                        ][8]
                        conf_hub[CONF_SENSORS][i][CONF_SCALE] = HUAWEI_SENSORS[entry][9]
                        conf_hub[CONF_SENSORS][i][CONF_OFFSET] = HUAWEI_SENSORS[entry][
                            10
                        ]
                        conf_hub[CONF_SENSORS][i][CONF_PRECISION] = HUAWEI_SENSORS[
                            entry
                        ][11]
                    elif conf_hub[CONF_BRAND] == "solaredge":
                        conf_hub[CONF_SENSORS][i][CONF_NAME] = SOLAREDGE_SENSORS[entry][
                            0
                        ]
                        conf_hub[CONF_SENSORS][i][CONF_DATA_TYPE] = SOLAREDGE_SENSORS[
                            entry
                        ][1]
                        conf_hub[CONF_SENSORS][i][
                            CONF_UNIT_OF_MEASUREMENT
                        ] = SOLAREDGE_SENSORS[entry][2]
                        conf_hub[CONF_SENSORS][i][CONF_ADDRESS] = SOLAREDGE_SENSORS[
                            entry
                        ][4]
                        conf_hub[CONF_SENSORS][i][CONF_COUNT] = SOLAREDGE_SENSORS[
                            entry
                        ][5]
                        conf_hub[CONF_SENSORS][i][
                            CONF_DEVICE_CLASS
                        ] = SOLAREDGE_SENSORS[entry][6]
                        conf_hub[CONF_SENSORS][i][CONF_INPUT_TYPE] = SOLAREDGE_SENSORS[
                            entry
                        ][7]
                        conf_hub[CONF_SENSORS][i][
                            CONF_REVERSE_ORDER
                        ] = SOLAREDGE_SENSORS[entry][8]
                        conf_hub[CONF_SENSORS][i][CONF_SCALE] = SOLAREDGE_SENSORS[
                            entry
                        ][9]
                        conf_hub[CONF_SENSORS][i][CONF_OFFSET] = SOLAREDGE_SENSORS[
                            entry
                        ][10]
                        conf_hub[CONF_SENSORS][i][CONF_PRECISION] = SOLAREDGE_SENSORS[
                            entry
                        ][11]

                    conf_hub[CONF_SENSORS][i][CONF_SLAVE] = conf_hub[CONF_SLAVE]
                    conf_hub[CONF_SENSORS][i][CONF_BRAND] = conf_hub[CONF_BRAND]
                    conf_hub[CONF_SENSORS][i][CONF_TYPE] = entry
                    conf_hub[CONF_SENSORS][i][CONF_SCAN_INTERVAL] = conf_hub[
                        CONF_SCAN_INTERVAL
                    ]
                    i += 1

        hub_collect[conf_hub[CONF_BRAND]] = ModbusHub(conf_hub)

        # modbus needs to be activated before components are loaded
        # to avoid a racing problem
        hub_collect[conf_hub[CONF_BRAND]].setup()

        # load platforms
        for component, conf_key in ((CONF_SENSOR, CONF_SENSORS),):
            if conf_key in conf_hub:
                load_platform(hass, component, DOMAIN, conf_hub, config)

    def stop_modbus(event):
        """Stop Modbus service."""
        for client in hub_collect.values():
            client.close()

    # register function to gracefully stop modbus
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop_modbus)

    return True


class ModbusHub:
    """Thread safe wrapper class for pymodbus."""

    def __init__(self, client_config):
        """Initialize the Modbus hub."""

        # generic configuration
        self._client = None
        self._lock = threading.Lock()
        self._config_name = client_config[CONF_NAME]
        self._config_brand = client_config[CONF_BRAND]
        self._config_port = client_config[CONF_PORT]
        self._config_timeout = client_config[CONF_TIMEOUT]
        self._config_delay = 0

        # network configuration
        self._config_host = client_config[CONF_HOST]
        self._config_delay = client_config[CONF_DELAY]
        if self._config_delay > 0:
            _LOGGER.warning("Parameter delay is accepted but not used in this version")
        _LOGGER.debug("Really setup modbushub")

    @property
    def name(self):
        """Return the name of this hub."""
        return self._config_brand

    def setup(self):
        """Set up pymodbus client."""

        if self._config_brand in ["huawei", "solaredge"]:
            self._client = ModbusTcpClient(
                host=self._config_host,
                port=self._config_port,
                timeout=self._config_timeout,
            )

        else:
            assert False

        # Connect device
        self.connect()

    def close(self):
        """Disconnect client."""
        with self._lock:
            self._client.close()

    def connect(self):
        """Connect client."""
        with self._lock:
            self._client.connect()
            sleep(0.05)

    def read_input_registers(self, unit, address, count):
        """Read input registers."""
        with self._lock:
            kwargs = {"unit": unit} if unit else {}
            return self._client.read_input_registers(address, count, **kwargs)

    def read_holding_registers(self, unit, address, count):
        """Read holding registers."""
        with self._lock:
            kwargs = {"unit": unit} if unit else {}
            return self._client.read_holding_registers(address, count, **kwargs)
