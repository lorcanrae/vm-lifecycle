import click

from vm_lifecycle.commands.config import config


@click.group()
def cli():
    """CLI tool to manage GCP VM lifecycle"""
    pass


cli.add_command(config)


# Commands to add
# create
# connect
# start
# stop
# status
# destroy

if __name__ == "__main__":
    cli()
