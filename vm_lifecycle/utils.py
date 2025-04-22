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


def pre_run_checks(workspace: str) -> bool:
    # Compare config with .tfvars
    config = load_config(DEFAULT_CONFIG_PATH)

    validate_tfvars_with_config(config=config, workspace=workspace)

    # Check if .terraform/ and .terraform.lock.hcl exists in workspace
    workspace_dir = Path(__file__).parent.parent / "infra" / workspace
    file_check = [".terraform", ".terraform.lock.hcl"]
    for file in file_check:
        if workspace_dir / file not in workspace_dir.iterdir():
            click.echo(
                f"{file} not found in {workspace}. Run `devm init tf --{workspace}` or `devm init tf`"
            )
            return False
    return True


def validate_tfvars_with_config(config: dict, workspace: str) -> bool:
    """
    Compare values in `config.yaml` with `terraform.tfvars` file in a given workspace.

    Returns:
    - True: if match
    - False: otherwise
    """

    tfvars_path = Path(f"infra/{workspace}/terraform.tfvars")

    if not tfvars_path.exists():
        click.echo(f"❌ tfvars file not found at {tfvars_path}.")
        click.echo(f"Run `vmlc init tf --workspace={workspace}` or `vmlc init tf`")
        return False

    with tfvars_path.open("r") as f:
        tfvars_lines = [line.strip() for line in f.readlines()]

    print(tfvars_lines)
    tfvars = {}
    for line in tfvars_lines:
        line = line.strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"')
        tfvars[key] = value if not value.isdigit() else int(value)

    mismatches = []
    for key, value in config.items():
        if key == "disk_size" and workspace != "vm-create":
            continue
        tfval = tfvars.get(key)
        if str(tfval) != str(value):
            mismatches.append((key, value, tfval))

    if mismatches:
        click.echo("❌ Mismatches found between config.yaml and terraform.tfvars:")
        for key, expected, actual in mismatches:
            click.echo(f"   - {key}: expected '{expected}', found '{actual}'")
        return False

    return True


def get_root_dir(file: Path):
    return Path(file).resolve().parent.parent.parent


def remove_tfstate_files(path: Path):
    for file in ["terraform.tfstate", "terraform.tfstate.backup"]:
        f = path / file
        if f.exists():
            f.unlink()
            click.echo(f"🗑️ Removed {f}")


if __name__ == "__main__":
    config = load_config(DEFAULT_CONFIG_PATH)
    print(config)
    # validate_tfvars_with_config(config, "vm-create")
