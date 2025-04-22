from pathlib import Path

##### Paths


ROOT_DIR = Path(__file__).parent.parent
DEFAULT_CONFIG_PATH = ROOT_DIR / "config.yaml"

##### Misc lists

TF_WORKSPACES = ["vm-create", "vm-archive", "vm-restore"]

GCP_MACHINE_TYPES = [
    "e2-micro",
    "e2-small",
    "e2-medium",
    "e2-standard-2",
    "e2-standard-4",
    "n1-standard-1",
    "n1-standard-2",
    "n2-standard-2",
    "n2-standard-4",
]
