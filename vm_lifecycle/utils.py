import click
import re
import subprocess
from typing import List, Optional
import threading
import itertools
import sys
import time
from contextlib import contextmanager

from vm_lifecycle.compute_manager import GCPComputeManager
from vm_lifecycle.config_manager import ConfigManager


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


######## GCP init context
def init_gcp_context(zone_override: str = None, check_apis: bool = True):
    config_manager = ConfigManager()

    if not config_manager.pre_run_profile_check():
        click.echo("❗ Error with active profile. Ensure a profile has been created.")
        return None, None, None

    active_zone = zone_override or config_manager.active_profile["zone"]
    compute_manager = GCPComputeManager(
        config_manager.active_profile["project_id"], active_zone
    )

    if check_apis and not config_manager.active_profile.get("api_cache", False):
        apis = compute_manager.check_required_apis()
        if apis["missing"]:
            click.echo("❗ The following GCP API's have not been enabled:")
            for api in apis["missing"]:
                click.echo(f"\t{api}")
            return None, None, None
        config_manager.config[config_manager.active]["api_cache"] = True
        config_manager.save_config()
    return config_manager, compute_manager, active_zone


######## Spinner
@contextmanager
def spinner(
    text: str = "",
    done_text: str = "✅ Operation Complete!",
    fail_text: str = "❗ Operation Failed!",
):
    stop_event = threading.Event()
    spinner_exception = []
    text_padding = max(2 + len(text), len(done_text)) + 2
    start_time = time.time()

    def spinner_task():
        spin = itertools.cycle(["-", "\\", "|", "/"])
        # start_time = time.time()
        while not stop_event.is_set():
            elapsed = int(time.time() - start_time)
            output = f"{next(spin)} {text.ljust(text_padding)} ({elapsed}s)"
            sys.stdout.write("\r" + output)
            sys.stdout.flush()
            time.sleep(0.1)
        # Clear the line after stopping
        clear_line = "\r" + " " * (text_padding + 20) + "\r"
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
        sys.stdout.write(f"\r{fail_text}\n")
        raise e
    else:
        stop_event.set()
        thread.join()
        sys.stdout.write(f"\r{done_text} ({int(time.time() - start_time)}s)\n")
    finally:
        pass


def poll_with_spinner(
    compute_manager: GCPComputeManager,
    op_name: str,
    text: str,
    scope: str,
    zone: str = None,
    done_text: str = "✅ Operation Complete!",
    fail_text: str = "❗ Operation Failed!",
):
    try:
        with spinner(text=text, done_text=done_text, fail_text=fail_text):
            gen = compute_manager.wait_for_operation(op_name, scope, zone=zone)
            while True:
                try:
                    update = next(gen)
                    if update == "RUNNING":
                        continue
                    elif isinstance(update, dict):
                        if not update.get("success", True):
                            raise RuntimeError("GCP Operation completed with errors")
                        return update
                except StopIteration as stop:
                    update = stop.value
                    if not update.get("succes", True):
                        raise RuntimeError("GCP Operation completed with errors")
                    return update
    except Exception as e:
        print("Error during polling: ", str(e))
        return {"success": False, "error": str(e)}


######## VSCode
def create_vscode_ssh():
    subprocess.run(["gcloud", "compute", "config-ssh"])


if __name__ == "__main__":
    pass
