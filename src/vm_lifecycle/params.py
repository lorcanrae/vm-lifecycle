from pathlib import Path

##### Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = ROOT_DIR / "config.yaml"

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
    print(ROOT_DIR)
