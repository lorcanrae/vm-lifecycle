from pathlib import Path
import subprocess
import yaml
import click
from vm_lifecycle.utils import (
    get_root_dir,
    write_tfvars_from_config,
    load_config,
    is_valid_instance_name,
    is_valid_project_id,
    prompt_validation,
)
import shutil
import os

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "config.yaml"


@click.group(name="init", invoke_without_command=True)
@click.pass_context
def init(ctx):
    """Initialization commands"""
    if ctx.invoked_subcommand is None:
        click.echo("Running default: init config and init tf")
        ctx.invoke(init_config)
        ctx.invoke(init_tf)


@init.command(name="config")
def init_config():
    """Prompt the user for config values and write to config.yaml"""
    click.echo("🔧 Initializing Terraform CLI config")

    config = {
        "project_id": prompt_validation(
            "GCP Project ID",
            is_valid_project_id,
            "Project ID must be 6-30 lowercase letters, digits or hyphens, starting with a character and not ending with a hyphen.",
        ),
        "zone": click.prompt("GCP zone", type=str, default="europe-west1-b"),
        "instance_name": prompt_validation(
            "VM instance name",
            is_valid_instance_name,
            "Instance name must be 1-63 characters, lowercase letters, digits or hyphens, start with a letter, and not end with a hyphen.",
        ),
        "instance_user": click.prompt(
            "Instance User. Recommend current local user ",
            type=str,
            default=os.environ.get("USER"),
        ),
        "machine_type": click.prompt("Machine type", type=str, default="e2-standard-4"),
        "disk_size": click.prompt("Disk size", type=int, default=100),
    }

    # Derive additional config
    config["region"] = "-".join(config["zone"].split("-")[:-1])
    config["image_base_name"] = config["instance_name"] + "-image"

    with DEFAULT_CONFIG_PATH.open("w") as f:
        yaml.dump(config, f)

    click.echo(f"✅ Configuration written to {DEFAULT_CONFIG_PATH}\n")

    click.echo("📦 Creating 'terraform.tfvars' for all workspaces")
    for workspace in ["vm-create", "vm-archive", "vm-restore"]:
        write_tfvars_from_config(config, workspace)
    click.echo("✅ 'terraform.tfvars' created in all workspaces\n")


@init.command(name="tf")
def init_tf():
    """Initialise Terraform workspace"""
    click.echo("Checking if 'terraform' is on PATH")
    terraform_path = shutil.which("terraform")
    if terraform_path:
        print(f"✅ Terraform is on PATH: {terraform_path}")
    else:
        print(
            "❌ Terraform is NOT on PATH.\nInstall terraform locally before proceeding."
        )
        return False

    click.echo("🔧 Initializing Terraform workspaces")
    root = get_root_dir(__file__)
    subprocess.run(["make", "-s", "init-all"], check=True, cwd=root)


@init.command(name="tfvars")
def create_tfvars_from_config():
    config = load_config(DEFAULT_CONFIG_PATH)
    for workspace in ["vm-create", "vm-archive", "vm-restore"]:
        write_tfvars_from_config(config=config, workspace=workspace)


@init.command(name="show")
def show_config():
    # Make sure config exists
    config = load_config(DEFAULT_CONFIG_PATH)

    for key, val in config.items():
        click.echo(f"{key}: {val}")


@init.command(name="clear-state")
def clear_tf_state():
    pass


if __name__ == "__main__":
    pass
