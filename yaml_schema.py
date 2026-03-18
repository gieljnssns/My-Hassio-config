import os
import glob
import subprocess

# Basispad van je Home Assistant config
BASE_PATH = "/Users/giel/Dev/My-Hassio"
# Pad van de JSON-schema repo
SCHEMA_REPO = os.path.join(BASE_PATH, "hass-json-schema")
SCHEMA_REPO_URL = "https://git.sr.ht/~johnhamelink/hass-json-schema"

# Update of clone de repository
if os.path.exists(SCHEMA_REPO):
    print("Updating hass-json-schema repository...")
    subprocess.run(["git", "-C", SCHEMA_REPO, "pull"], check=True)
else:
    print("Cloning hass-json-schema repository...")
    subprocess.run(["git", "clone", SCHEMA_REPO_URL, SCHEMA_REPO], check=True)

# Mapping van YAML bestanden (of glob patterns) naar JSON-schema's
SCHEMA_MAP = {
    "config/configuration.yaml": "configuration.json",

    # Automations
    "config/automations.yaml": "integration-automation.json",
    "config/automation/**/*.yaml": "integration-automation.json",

    # Scripts
    "config/scripts.yaml": "integration-script.json",
    "config/scripts/**/*.yaml": "integration-script.json",

    # Blueprints
    "config/blueprints/automation/**/*.yaml": "blueprint-automation.json",
    "config/blueprints/script/**/*.yaml": "blueprint-script.json",
    "config/blueprints/template/**/*.yaml": "blueprint-template.json",
    "config/custom_templates/**/*.yaml": "blueprint-template.json",

    # Integrations / Groups
    "config/integrations/sensors/**/*.yaml": "integration-sensor.json",
    "config/integrations/binary_sensors/**/*.yaml": "integration-binary_sensor.json",
    "config/integrations/input_boolean/**/*.yaml": "integration-input_boolean.json",
    "config/integrations/input_datetime/**/*.yaml": "integration-input_datetime.json",
    "config/integrations/input_select/**/*.yaml": "integration-input_select.json",
    "config/integrations/input_text/**/*.yaml": "integration-input_text.json",
    "config/integrations/templates/**/*.yaml": "integration-template.json",
    "config/integrations/alarm/**/*.yaml": "integration-alarm_control_panel.json",

    # Packages
    "config/packages/**/*.yaml": "integration-homeassistant-packages.json",
}

# Pad naar de JSON-schema's
SCHEMA_BASE = os.path.join(SCHEMA_REPO, "json-schemas")

# Functie om YAML bestanden te vinden en $schema toe te voegen
for pattern, schema_file in SCHEMA_MAP.items():
    # Gebruik glob om bestanden te vinden (recursive=True voor **)
    full_pattern = os.path.join(BASE_PATH, pattern)
    for file_path in glob.glob(full_pattern, recursive=True):
        if not os.path.isfile(file_path):
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Maak de $schema regel met file:/// prefix
        schema_line = f"# yaml-language-server: $schema=file://{os.path.join(SCHEMA_BASE, schema_file)}\n"

        # Voeg alleen toe als het nog niet aanwezig is
        if lines and lines[0].strip() == schema_line.strip():
            continue

        # Voeg $schema bovenaan
        lines.insert(0, schema_line)

        # Schrijf terug naar het bestand
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"Updated schema in: {file_path}")
