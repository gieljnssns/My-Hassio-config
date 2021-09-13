"""Support for Modbus."""
from time import sleep
import logging
import threading

from pymodbus.client.sync import ModbusSerialClient, ModbusTcpClient, ModbusUdpClient
from pymodbus.transaction import ModbusRtuFramer

from homeassistant.const import (
    ATTR_STATE,
    CONF_COVERS,
    CONF_DELAY,
    CONF_HOST,
    CONF_METHOD,
    CONF_NAME,
    CONF_PORT,
    CONF_TIMEOUT,
    CONF_TYPE,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.helpers.discovery import load_platform

from .const import (
    ATTR_ADDRESS,
    ATTR_HUB,
    ATTR_UNIT,
    ATTR_VALUE,
    CONF_BAUDRATE,
    CONF_BINARY_SENSOR,
    CONF_BINARY_SENSORS,
    CONF_BYTESIZE,
    CONF_CLIMATE,
    CONF_CLIMATES,
    CONF_COVER,
    CONF_PARITY,
    CONF_SENSOR,
    CONF_SENSORS,
    CONF_STOPBITS,
    CONF_SWITCH,
    CONF_SWITCHES,
    MODBUS_DOMAIN as DOMAIN,
    SERVICE_WRITE_COIL,
    SERVICE_WRITE_REGISTER,
)

_LOGGER = logging.getLogger(__name__)


def modbus_setup(
    hass, config, service_write_register_schema, service_write_coil_schema
):
    """Set up Modbus component."""
    hass.data[DOMAIN] = hub_collect = {}

    for conf_hub in config[DOMAIN]:
        hub_collect[conf_hub[CONF_NAME]] = ModbusHub(conf_hub)

        # modbus needs to be activated before components are loaded
        # to avoid a racing problem
        hub_collect[conf_hub[CONF_NAME]].setup()

        # load platforms
        for component, conf_key in (
            (CONF_CLIMATE, CONF_CLIMATES),
            (CONF_COVER, CONF_COVERS),
            (CONF_BINARY_SENSOR, CONF_BINARY_SENSORS),
            (CONF_SENSOR, CONF_SENSORS),
            (CONF_SWITCH, CONF_SWITCHES),
        ):
            if conf_key in conf_hub:
                load_platform(hass, component, DOMAIN, conf_hub, config)

    def stop_modbus(event):
        """Stop Modbus service."""
        for client in hub_collect.values():
            client.close()

    def write_register(service):
        """Write Modbus registers."""
        unit = int(float(service.data[ATTR_UNIT]))
        address = int(float(service.data[ATTR_ADDRESS]))
        value = service.data[ATTR_VALUE]
        client_name = service.data[ATTR_HUB]
        if isinstance(value, list):
            hub_collect[client_name].write_registers(
                unit, address, [int(float(i)) for i in value]
            )
        else:
            hub_collect[client_name].write_register(unit, address, int(float(value)))

    def write_coil(service):
        """Write Modbus coil."""
        unit = service.data[ATTR_UNIT]
        address = service.data[ATTR_ADDRESS]
        state = service.data[ATTR_STATE]
        client_name = service.data[ATTR_HUB]
        hub_collect[client_name].write_coil(unit, address, state)

    # register function to gracefully stop modbus
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop_modbus)

    # Register services for modbus
    hass.services.register(
        DOMAIN,
        SERVICE_WRITE_REGISTER,
        write_register,
        schema=service_write_register_schema,
    )
    hass.services.register(
        DOMAIN, SERVICE_WRITE_COIL, write_coil, schema=service_write_coil_schema
    )
    return True


class ModbusHub:
    """Thread safe wrapper class for pymodbus."""

    def __init__(self, client_config):
        """Initialize the Modbus hub."""

        # generic configuration
        self._client = None
        self._lock = threading.Lock()
        self._config_name = client_config[CONF_NAME]
        self._config_type = client_config[CONF_TYPE]
        self._config_port = client_config[CONF_PORT]
        self._config_timeout = client_config[CONF_TIMEOUT]
        self._config_delay = 0

        if self._config_type == "serial":
            # serial configuration
            self._config_method = client_config[CONF_METHOD]
            self._config_baudrate = client_config[CONF_BAUDRATE]
            self._config_stopbits = client_config[CONF_STOPBITS]
            self._config_bytesize = client_config[CONF_BYTESIZE]
            self._config_parity = client_config[CONF_PARITY]
        else:
            # network configuration
            self._config_host = client_config[CONF_HOST]
            self._config_delay = client_config[CONF_DELAY]
            if self._config_delay > 0:
                _LOGGER.warning(
                    "Parameter delay is accepted but not used in this version"
                )

    @property
    def name(self):
        """Return the name of this hub."""
        return self._config_name

    def setup(self):
        """Set up pymodbus client."""
        if self._config_type == "serial":
            self._client = ModbusSerialClient(
                method=self._config_method,
                port=self._config_port,
                baudrate=self._config_baudrate,
                stopbits=self._config_stopbits,
                bytesize=self._config_bytesize,
                parity=self._config_parity,
                timeout=self._config_timeout,
                retry_on_empty=True,
            )
        elif self._config_type == "rtuovertcp":
            self._client = ModbusTcpClient(
                host=self._config_host,
                port=self._config_port,
                framer=ModbusRtuFramer,
                timeout=self._config_timeout,
            )
        elif self._config_type == "tcp":
            self._client = ModbusTcpClient(
                host=self._config_host,
                port=self._config_port,
                timeout=self._config_timeout,
            )
        elif self._config_type == "udp":
            self._client = ModbusUdpClient(
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

    def read_coils(self, unit, address, count):
        """Read coils."""
        with self._lock:
            kwargs = {"unit": unit} if unit else {}
            return self._client.read_coils(address, count, **kwargs)

    def read_discrete_inputs(self, unit, address, count):
        """Read discrete inputs."""
        with self._lock:
            kwargs = {"unit": unit} if unit else {}
            return self._client.read_discrete_inputs(address, count, **kwargs)

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

    def write_coil(self, unit, address, value):
        """Write coil."""
        with self._lock:
            kwargs = {"unit": unit} if unit else {}
            self._client.write_coil(address, value, **kwargs)

    def write_register(self, unit, address, value):
        """Write register."""
        with self._lock:
            kwargs = {"unit": unit} if unit else {}
            self._client.write_register(address, value, **kwargs)

    def write_registers(self, unit, address, values):
        """Write registers."""
        with self._lock:
            kwargs = {"unit": unit} if unit else {}
            self._client.write_registers(address, values, **kwargs)
