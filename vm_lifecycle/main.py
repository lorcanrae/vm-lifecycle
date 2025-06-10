import click

from vm_lifecycle.commands.profile import profile
from vm_lifecycle.commands.create import create_vm_instance
from vm_lifecycle.commands.destroy import destroy_vm


@click.group()
def cli():
    """CLI tool to manage GCP VM lifecycle"""
    pass


cli.add_command(profile)
cli.add_command(create_vm_instance)
cli.add_command(destroy_vm)

# Commands to add
# connect
# start
# stop
# status
# destroy

if __name__ == "__main__":
    cli()
