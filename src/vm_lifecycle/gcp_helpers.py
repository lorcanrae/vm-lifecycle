import click

from vm_lifecycle.compute_manager import GCPComputeManager
from vm_lifecycle.config_manager import ConfigManager
from vm_lifecycle.utils import spinner


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
