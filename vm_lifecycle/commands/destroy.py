import click
import sys

from vm_lifecycle.gcp_helpers import poll_with_spinner, init_gcp_context
from vm_lifecycle.utils import select_from_list, spinner


@click.command(name="destroy")
@click.option("-v", "--vm", is_flag=True, help="Destroy all VM Instances")
@click.option("-i", "--images", is_flag=True, help="Destroy VM Images")
def destroy_vm_instance(vm, images):
    """Destroy GCP VM instance"""
    config_manager, compute_manager, active_zone = init_gcp_context()
    if not config_manager:
        sys.exit(1)

    if vm:
        # Load profile and extract regions
        profile_regions = []
        for k, v in config_manager.config.items():
            if k == "active":
                continue
            profile_regions.append(v["region"])

        active_continents = list(
            set([region.split("-")[0] for region in profile_regions])
        )

        with spinner(
            text=f"Searching for VM instances in {', '.join([c.title() for c in active_continents])}...",
            done_text="Found the following instances:",
        ):
            # Get list of zones
            gcp_zones = compute_manager._list_zones()
            target_zones = [
                zone for zone in gcp_zones if zone.split("-")[0] in active_continents
            ]

            # check for instances in each zone
            instances = []
            for zone in target_zones:
                zone_instances = compute_manager.list_instances(zone)
                if zone_instances:
                    for zone_instance in zone_instances:
                        instances.append((zone_instance["name"], zone))

        selected = select_from_list(
            list_opt=instances + ["all instances", "exit"],
            prompt_message="❓ Select image to destroy",
        )

        if selected == "exit":
            click.echo("❌ Aborted.")
            sys.exit(1)
        elif selected == "all instances":
            # First check
            if not click.confirm(
                "❓ Do you really want to destroy all instances?", default=False
            ):
                click.echo("❌ Aborted.")
                sys.exit(1)
            # Second check
            if not click.confirm(
                "❓ Do you really, REALLY want to destroy all VM instances? This is action can not be reversed",
                default=False,
            ):
                click.echo("❌ Aborted.")
                sys.exit(1)

            for instance_name, instance_zone in instances:
                op = compute_manager.delete_instance(
                    instance_name=instance_name, zone=instance_zone
                )

                spinner_text = f"Destroying VM instance: {instance_name} in zone: '{instance_zone}'"
                done_text = f"🗑️ VM instance: '{instance_name}' in zone: '{instance_zone}' destroyed."

                poll_with_spinner(
                    compute_manager=compute_manager,
                    op_name=op["name"],
                    text=spinner_text,
                    done_text=done_text,
                    scope="zone",
                    zone=active_zone,
                )
        elif isinstance(selected, tuple) and len(selected) == 2:
            instance_name, instance_zone = selected
            op = compute_manager.delete_instance(
                instance_name=instance_name, zone=instance_zone
            )

            spinner_text = (
                f"Destroying VM instance: '{instance_name}' in zone: '{instance_zone}'"
            )
            done_text = f"🗑️ VM instance: '{instance_name}' in zone: '{instance_zone}' destroyed."

            poll_with_spinner(
                compute_manager=compute_manager,
                op_name=op["name"],
                text=spinner_text,
                done_text=done_text,
                scope="zone",
                zone=active_zone,
            )

        else:
            click.echo("❌ Invalid selection.")
            sys.exit(1)
        sys.exit(0)

    ### Images
    if images:
        # Get a list of all images
        images = [img["name"] for img in compute_manager.list_images()]

        click.echo("🔎 Images found:")

        # Confirm to select from list, all (with confirmation), or quit
        selected = select_from_list(
            list_opt=images + ["all images", "exit"],
            prompt_message="❓ Select image to destroy",
        )

        if selected == "exit":
            click.echo("❌ Aborted.")
            sys.exit(1)
        elif selected == "all images":
            # First check
            if not click.confirm(
                "❓ Do you really want to destroy all images?", default=False
            ):
                click.echo("❌ Aborted.")
                sys.exit(1)
            # Second check
            if not click.confirm(
                "❓ Do you really, REALLY want to destroy all images? This is action can not be reversed",
                default=False,
            ):
                click.echo("❌ Aborted.")
                sys.exit(1)

            for image in images:
                op = compute_manager.delete_image(image)

                spinner_text = f"Destroying image: '{image}'"
                done_text = f"🗑️ Image: '{image}' destroyed"

                poll_with_spinner(
                    compute_manager=compute_manager,
                    op_name=op["name"],
                    text=spinner_text,
                    done_text=done_text,
                    scope="global",
                )
        else:
            op = compute_manager.delete_image(selected)

            spinner_text = f"Destroying image: '{selected}'"
            done_text = f"🗑️ Image: '{selected}' destroyed"

            poll_with_spinner(
                compute_manager=compute_manager,
                op_name=op["name"],
                text=spinner_text,
                done_text=done_text,
                scope="global",
            )

        sys.exit(0)

    # Check Instance exists
    existing_instances = compute_manager.list_instances()

    if not existing_instances:
        click.echo(
            f"❗ No GCP Compute Engine instances found in zone: '{config_manager.active_profile['zone']}'."
        )
        sys.exit(1)

    for instance in existing_instances:
        if instance["name"] == config_manager.active_profile["instance_name"]:
            if click.confirm(
                f"❓ Destroy instance: '{config_manager.active_profile['instance_name']}' in zone: '{active_zone}'?",
                default=False,
            ):
                op = compute_manager.delete_instance(
                    instance_name=config_manager.active_profile["instance_name"],
                    zone=active_zone,
                )
            else:
                click.echo("❌ Aborted.")
                sys.exit(1)

    spinner_text = f"Destroying VM instance: '{config_manager.active_profile['instance_name']}' in zone: '{config_manager.active_profile['zone']}'"
    done_text = f"🗑️ VM instance: '{config_manager.active_profile['instance_name']}' in zone: '{active_zone}' destroyed."

    poll_with_spinner(
        compute_manager=compute_manager,
        op_name=op["name"],
        text=spinner_text,
        done_text=done_text,
        scope="zone",
        zone=active_zone,
    )
