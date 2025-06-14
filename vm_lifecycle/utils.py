import click
import re
import subprocess
from typing import List, Optional
import threading
import itertools
import sys
import time
from contextlib import contextmanager
from googleapiclient.errors import HttpError
from functools import wraps

# from vm_lifecycle.compute_manager import GCPComputeManager
# from vm_lifecycle.config_manager import ConfigManager


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


######## Click Select from List
def select_from_list(
    list_opt: List[str],
    prompt_message: str,
    confirm_message_fn: Optional[callable] = None,
    confirm: bool = False,
    default: Optional[int] = None,
):
    if not list_opt:
        click.echo("❌ No items available.")
        return None

    # List profiles
    for i, p in enumerate(list_opt, 1):
        click.echo(f"[{i}] {p}")
    while True:
        try:
            default_display = default + 1 if default is not None else None
            idx = click.prompt(prompt_message, type=int, default=default_display)
            if 1 <= idx <= len(list_opt):
                selection = list_opt[idx - 1]
                if confirm:
                    confirm_msg = (
                        confirm_message_fn(selection)
                        if confirm_message_fn
                        else f"❓ Are you sure you want to select '{selection}'?"
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


######## Error handling
def gcphttperror():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except HttpError as e:
                click.echo(f"❗ GCP API Error: {e}")
                sys.exit(1)

        return wrapper

    return decorator


######## Spinner
@contextmanager
def spinner(
    text: str = "",
    done_text: str = "✅ Operation Complete!",
    fail_text: str = "❗ Operation Failed!",
    max_duration: int = 900,
):
    stop_event = threading.Event()
    spinner_exception = []
    spin_padding = 2
    text_padding = max(spin_padding + len(text), len(done_text))
    start_time = time.time()
    max_elapsed_width = len(str(max_duration))

    def spinner_task():
        spin = itertools.cycle(["-", "\\", "|", "/"])
        # start_time = time.time()
        while not stop_event.is_set():
            elapsed = int(time.time() - start_time)

            output = f"{next(spin)} {text.ljust(text_padding - spin_padding)} ({str(elapsed).rjust(max_elapsed_width)}s)"
            sys.stdout.write("\r" + output)
            sys.stdout.flush()
            time.sleep(0.1)
        # Clear the line after stopping
        clear_line = "\r" + " " * (text_padding + max_elapsed_width + 10) + "\r"
        sys.stdout.write(clear_line)
        sys.stdout.flush()

    thread = threading.Thread(target=spinner_task)
    thread.start()

    try:
        yield
    except KeyboardInterrupt as e:
        spinner_exception.append(e)
        stop_event.set()
        thread.join()
        sys.stdout.write("\r")
        sys.stdout.flush()
        print("\n❗ Operation cancelled.")
        raise e
    except Exception as e:
        stop_event.set()
        thread.join()
        elapsed = int(time.time() - start_time)
        sys.stdout.write(
            f"\r{fail_text.ljust(text_padding)} ({str(elapsed).rjust(max_elapsed_width)})\n"
        )
        raise e
    else:
        stop_event.set()
        thread.join()
        elapsed = int(time.time() - start_time)
        sys.stdout.write(
            f"\r{done_text.ljust(text_padding)} ({str(elapsed).rjust(max_elapsed_width)}s)\n"
        )
    finally:
        pass


######## VSCode
def create_vm_ssh_connection(project_id: str, instance_name: str, zone: str):
    result = subprocess.run(
        ["gcloud", "compute", "config-ssh"], capture_output=True, text=True
    )

    # Access output and errors
    output = result.stdout
    error = result.stderr

    # Example logic: parse and conditionally print
    if result.returncode != 0:
        print(f"❗ Error running gcloud: {error}")
        sys.exit(1)

    # Parse output as needed
    for line in output.splitlines():
        if f"{instance_name}.{zone}.{project_id}" in line:
            print(
                f"✅ Created connection to instance: {instance_name}.{zone}.{project_id}"
            )
        if "Warning" in line:
            print(f"⚠️ {line}")
        elif "Updated" in line or "Added" in line:
            print(f"✅ {line}")
        # Add custom filters or logic here

    # Optionally return output if needed for further processing
    return output


if __name__ == "__main__":
    pass
