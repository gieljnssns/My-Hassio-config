"""Constants used in modbus integration."""

# from homeassistant.const import (
#     ATTR_DEVICE_CLASS,
#     ATTR_ICON,
#     ATTR_UNIT_OF_MEASUREMENT,
#     DEVICE_CLASS_BATTERY,
#     DEVICE_CLASS_ENERGY,
#     DEVICE_CLASS_POWER,
#     ENERGY_KILO_WATT_HOUR,
#     PERCENTAGE,
#     POWER_WATT,
# )

# configuration names
CONF_BRAND = "brand"
CONF_HUB = "hub"
CONF_HUAWEI = "huawei"
CONF_SOLAREDGE = "solaredge"
CONF_REGISTER = "register"
CONF_REGISTER_TYPE = "register_type"
CONF_REGISTERS = "registers"
CONF_REVERSE_ORDER = "reverse_order"
CONF_SCALE = "scale"
CONF_COUNT = "count"
CONF_PRECISION = "precision"
CONF_COILS = "coils"
DEFAULT_BRAND = "huawei"

# integration names
DEFAULT_HUB = "modbus_hub"
SOLAR_INVERTER_MODBUS_DOMAIN = "solar_inverter_modbus"

# data types
DATA_TYPE_CUSTOM = "custom"
DATA_TYPE_FLOAT = "float"
DATA_TYPE_INT = "int"
DATA_TYPE_UINT = "uint"
DATA_TYPE_STRING = "string"

# call types
CALL_TYPE_REGISTER_HOLDING = "holding"
CALL_TYPE_REGISTER_INPUT = "input"

# the following constants are TBD.
# changing those in general causes a breaking change, because
# the contents of configuration.yaml needs to be updated,
# therefore they are left to a later date.
# but kept here, with a reference to the file using them.

# __init.py
ATTR_ADDRESS = "address"
ATTR_HUB = "hub"
ATTR_UNIT = "unit"
ATTR_VALUE = "value"
# SERVICE_WRITE_COIL = "write_coil"
# SERVICE_WRITE_REGISTER = "write_register"
DEFAULT_SCAN_INTERVAL = 15  # seconds

# binary_sensor.py
# CONF_INPUTS = "inputs"
CONF_INPUT_TYPE = "input_type"

# sensor.py
CONF_DATA_TYPE = "data_type"
DEFAULT_STRUCT_FORMAT = {
    DATA_TYPE_INT: {1: "h", 2: "i", 4: "q"},
    DATA_TYPE_UINT: {1: "H", 2: "I", 4: "Q"},
    DATA_TYPE_FLOAT: {1: "e", 2: "f", 4: "d"},
}
CONF_SENSOR = "sensor"
CONF_SENSORS = "sensors"


# cover.py
# DEFAULT_SLAVE = 1
