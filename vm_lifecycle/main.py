import click

from vm_lifecycle.commands.profile import profile
from vm_lifecycle.commands.create import create_vm_instance
from vm_lifecycle.commands.destroy import destroy_vm_instance
from vm_lifecycle.commands.start import start_vm_instance
from vm_lifecycle.commands.stop import stop_vm_instance
from vm_lifecycle.commands.status import gcp_vm_instance_status


@click.group()
def cli():
    """CLI tool to manage GCP VM lifecycle"""
    pass


cli.add_command(profile)
cli.add_command(create_vm_instance)
cli.add_command(destroy_vm_instance)
cli.add_command(start_vm_instance)
cli.add_command(stop_vm_instance)
cli.add_command(gcp_vm_instance_status)

# TODO: Commands to add
# connect
# fix destroy


if __name__ == "__main__":
    cli()
