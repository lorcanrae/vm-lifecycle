from pathlib import Path
import yaml
import click

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> dict:
    if not path.exists():
        click.echo(
            f"Config file `config.yaml` not found at: {path}. Run `devm init config` to create config.yaml"
        )
        return {}

    with path.open("r") as f:
        config = yaml.safe_load(f)

    return config or {}


def write_tfvars_from_config(config: dict, workspace: str):
    tfvars_path = Path(f"infra/{workspace}/terraform.tfvars")

    with tfvars_path.open("w") as f:
        for key, value in config.items():
            if key == "disk_size" and workspace != "vm-create":
                continue
            f.write(f'{key} = "{value}"\n')


def pre_run_checks(workspace: str):
    # TODO: Compare config with .tfvars
    config = load_config(DEFAULT_CONFIG_PATH)

    # Check if .terraform/ and .terraform.lock.hcl exists in workspace
    workspace_dir = Path(__file__).parent.parent / "infra" / workspace
    file_check = [".terraform", ".terraform.lock.hcl"]
    for file in file_check:
        if workspace_dir / file not in workspace_dir.iterdir():
            click.echo(
                f"{file} not found in {workspace}. Run `devm init tf --{workspace}` or `devm init tf`"
            )
            return False


def validate_tfvars_with_config(config: dict, workspace: str):
    # TODO
    pass


def get_root_dir(file: Path):
    return Path(file).resolve().parent.parent.parent


def check_init_tf() -> bool:
    pass


if __name__ == "__main__":
    config = load_config(DEFAULT_CONFIG_PATH)

    write_tfvars_from_config(config, "vm-create")
