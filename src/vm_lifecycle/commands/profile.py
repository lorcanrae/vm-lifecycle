import click
import os
import sys
from vm_lifecycle.config_manager import ConfigManager
from vm_lifecycle.utils import (
    is_valid_profile_name,
    is_valid_instance_name,
    is_valid_project_id,
    prompt_validation,
    select_from_list,
)

from vm_lifecycle.params import GCP_MACHINE_TYPES


@click.group(name="profile")
def profile():
    """GCP VM Lifecycle profile Commands"""
    pass


@profile.command("create")
def create_profile():
    """Prompt for profile values and create a profile."""
    manager = ConfigManager()
    click.echo("🔧 Create CLI Profile")

    profile_name = prompt_validation(
        "Profile Name",
        is_valid_profile_name,
        "Invalid profile name.",
    )

    profile_config = {
        "project_id": prompt_validation(
            "GCP Project ID", is_valid_project_id, "Invalid project ID."
        ),
        "zone": click.prompt("GCP zone", type=str, default="europe-west1-b"),
        "instance_name": prompt_validation(
            "VM instance name", is_valid_instance_name, "Invalid instance name."
        ),
        "instance_user": click.prompt(
            "Instance User", type=str, default=os.environ.get("USER")
        ),
        "machine_type": click.prompt(
            "Machine type",
            type=click.Choice(GCP_MACHINE_TYPES),
            default="e2-standard-4",
        ),
        "disk_size": click.prompt("Disk size", type=int, default=100),
    }

    # Derive additional config
    profile_config["region"] = "-".join(profile_config["zone"].split("-")[:-1])
    profile_config["image_base_name"] = profile_config["instance_name"] + "-image"
    profile_config["api_cache"] = False

    overwrite = False
    if profile_name in manager.config:
        overwrite = click.confirm(
            f"❓ Profile: {profile_name} already exists, overwrite?", default=False
        )
        if not overwrite:
            click.echo("❌ Aborted.")
            sys.exit(1)

    manager.add_profile(profile_name, profile_config, overwrite=overwrite)
    click.echo(f"📁 Saving profile to: {manager.config_path}")

    all_profiles = list(manager.list_profiles().keys())
    if len(all_profiles) > 1:
        active = click.prompt(
            "Select active profile",
            type=click.Choice(all_profiles),
            default=profile_name,
        )
        manager.set_active_profile(active)

    if not manager.get_active_profile():
        manager.set_active_profile(profile_name)

    click.echo(f"\n✅ Profile '{profile_name}' added.")
    click.echo(f"✅ Active profile set to: '{manager.get_active_profile()}'")


@profile.command(name="show")
def list_profiles():
    manager = ConfigManager()
    profiles = manager.list_profiles()

    if not profiles:
        click.echo(
            f"❗ No profiles found in {manager.config_path}. Run 'vmlc config create' to create a profile."
        )
        sys.exit(1)

    for name, cfg in profiles.items():
        click.echo(f"\n{name}")
        for k, v in cfg.items():
            click.echo(f"  {k}: {v}")
    click.echo(f"\n Active profile: {manager.get_active_profile()}")


@profile.command(name="set")
@click.argument("profile_name", required=False)
def set_profile(profile_name):
    manager = ConfigManager()
    profiles = list(manager.list_profiles().keys())
    current = manager.get_active_profile()

    if not profiles:
        click.echo(
            f"❗ No profiles found in {manager.config_path}. Run 'vmlc config create' to create a profile."
        )
        sys.exit(1)

    if profile_name:
        if manager.set_active_profile(profile_name):
            click.echo(f"✅ Active profile set to: '{profile_name}'")
            sys.exit(0)
        else:
            click.echo(f"❌ Profile '{profile_name}' not found.")
            sys.exit(1)

    click.echo("Available profiles:")
    selected = select_from_list(
        list_opt=profiles,
        prompt_message="Enter profile number to activate",
        default=profiles.index(current) if current in profiles else None,
    )

    if selected:
        manager.set_active_profile(selected)
        click.echo(f"\n✅ Active profile set to: '{selected}'")
    return


@profile.command(name="delete")
@click.argument("profile_name", required=False)
@click.option("-a", "--all", "delete_all", is_flag=True, help="Delete all profiles")
def delete_profile(profile_name, delete_all):
    manager = ConfigManager()
    profiles = list(manager.list_profiles().keys())

    if delete_all:
        if not profiles:
            click.echo("No profiles to delete.")
            sys.exit(0)
        if click.confirm("❓  Delete all profiles?", default=False):
            manager.delete_all_profiles()
            click.echo("🗑️ All profiles deleted.")
        else:
            click.echo("❌ Aborted.")
        return

    # TODO: this looks wrong
    if profile_name:
        if not manager.delete_profile(profile_name) and click.confirm(
            f"❓ Delete profile: '{profile_name}'?"
        ):
            click.echo(f"❌ Profile '{profile_name}' not found.")
            sys.exit(1)
        else:
            click.echo(f"🗑️ Deleted profile '{profile_name}'")
            sys.exit(0)

    if not profile_name:
        selected = select_from_list(
            profiles=profiles,
            prompt_message="Enter the number of profile to delete",
            confirm=True,
            confirm_message_fn=lambda name: f"❓ Delete profile '{name}'?",
        )
        if selected:
            manager.delete_profile(selected)
            click.echo(f"\n🗑️ Deleted profile '{selected}'")
