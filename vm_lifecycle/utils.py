import click
import re
import subprocess
from typing import List, Optional


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


def select_from_list(
    profiles: List[str],
    prompt_message: str,
    confirm_message_fn: Optional[callable] = None,
    confirm: bool = False,
    default: Optional[int] = None,
):
    if not profiles:
        click.echo("❌ No items available.")
        return None

    # List profiles
    for i, p in enumerate(profiles, 1):
        click.echo(f"{i}. {p}")
    while True:
        try:
            default_display = default + 1 if default is not None else None
            idx = click.prompt(prompt_message, type=int, default=default_display)
            if 1 <= idx <= len(profiles):
                selection = profiles[idx - 1]
                if confirm:
                    confirm_msg = (
                        confirm_message_fn(selection)
                        if confirm_message_fn
                        else f"Are you sure you want to select '{selection}'?"
                    )
                    if not click.confirm(confirm_msg, default=False):
                        click.echo("❌ Aborted.")
                        return None
                return selection
            else:
                click.echo("❌ Invalid choice.")
        except (click.exceptions.Abort, KeyboardInterrupt):
            click.echo("\n❌ Aborted.")
            return
        except Exception:
            click.echo("❌ Invalid input.")
    return None


######## VSCode
def create_vscode_ssh():
    subprocess.run(["gcloud", "compute", "config-ssh"])


if __name__ == "__main__":
    pass
