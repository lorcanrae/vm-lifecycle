from pathlib import Path
from platformdirs import user_config_dir

##### Paths
APP_NAME = "vmlc"
CONFIG_DIR = Path(user_config_dir(APP_NAME))
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_CONFIG_PATH = CONFIG_DIR / "config.yaml"

##### GCP Misc lists
GCP_MACHINE_TYPES = [
    "e2-medium",
    "e2-standard-2",
    "e2-standard-4",
    "n1-standard-1",
    "n1-standard-2",
    "n2-standard-2",
    "n2-standard-4",
]

if __name__ == "__main__":
    print(DEFAULT_CONFIG_PATH)
