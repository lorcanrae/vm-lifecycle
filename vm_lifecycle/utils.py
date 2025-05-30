from pathlib import Path
import yaml
import click
import re
import subprocess
from vm_lifecycle.params import DEFAULT_CONFIG_PATH


######## Config
# Superseded


def load_config(path: Path = DEFAULT_CONFIG_PATH, warn: bool = True) -> dict:
    if not path.exists():
        if warn:
            click.echo(
                f"❗ 'config.yaml' not found at: {path}. Run 'vmlc config create' to create a profile in 'config.yaml'"
            )
        return {}

    with path.open("r") as f:
        config = yaml.safe_load(f)

    return config


######## Click Config Input Validation


def is_valid_profile_name(profile_id: str) -> bool:
    return re.match(r"^[a-z][a-z0-9\-]{1,20}[a-z0-9]$", profile_id) is not None


def is_valid_project_id(pid: str) -> bool:
    return re.match(r"^[a-z][a-z0-9\-]{4,28}[a-z0-9]$", pid) is not None


def is_valid_instance_name(name: str) -> bool:
    return re.match(r"^[a-z]([-a-z0-9]{0,61}[a-z0-9])?$", name) is not None


def prompt_validation(prompt_text, validator_fn, error_msg):
    while True:
        value = click.prompt(prompt_text, type=str)
        if validator_fn(value):
            return value
        click.echo(f"❌ {error_msg}\n")


######## VSCode


def create_vscode_ssh():
    subprocess.run(["gcloud", "compute", "config-ssh"])


if __name__ == "__main__":
    pass
