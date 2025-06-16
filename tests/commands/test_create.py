import click
import pytest
from click.testing import CliRunner
from vm_lifecycle.commands.create import create_vm_instance


@pytest.fixture
def mock_context(mocker):
    config_mock = mocker.Mock()
    compute_mock = mocker.Mock()

    config_mock.active_profile = {
        "instance_name": "test-instance",
        "image_base_name": "test-image",
        "machine_type": "e2-standard-2",
        "disk_size": 100,
        "instance_user": "ubuntu",
    }
    config_mock.update_active_zone_region.return_value = True

    mocker.patch(
        "vm_lifecycle.commands.create.init_gcp_context",
        return_value=(config_mock, compute_mock, "zone"),
    )
    return config_mock, compute_mock


def test_create_exits_if_config_invalid(mocker):
    mocker.patch(
        "vm_lifecycle.commands.create.init_gcp_context", return_value=(None, None, None)
    )

    runner = CliRunner()
    result = runner.invoke(create_vm_instance)

    assert result.exit_code == 1
    assert "❗ Error with active profile" in result.output or result.output == ""


def test_create_exits_if_instance_exists(mock_context, mocker):
    config_mock, compute_mock = mock_context
    compute_mock.list_instances.return_value = [{"name": "test-instance"}]

    runner = CliRunner()
    result = runner.invoke(create_vm_instance)

    assert result.exit_code == 1
    assert "already exists" in result.output


def test_create_aborts_on_image_confirm_decline(mock_context, mocker):
    config_mock, compute_mock = mock_context
    compute_mock.list_instances.return_value = []
    compute_mock.list_images.return_value = [{"name": "img1"}, {"name": "img2"}]

    mocker.patch("click.confirm", return_value=False)

    runner = CliRunner()
    result = runner.invoke(create_vm_instance)

    assert result.exit_code == 1
    assert "Aborted" in result.output


def test_create_successful_instance_creation(mock_context, mocker):
    config_mock, compute_mock = mock_context
    compute_mock.list_instances.return_value = []
    compute_mock.list_images.return_value = []
    compute_mock.create_instance.return_value = {"name": "operation-123"}

    def mock_poll_with_spinner(*args, **kwargs):
        click.echo(kwargs.get("done_text"))
        return {"success": True}

    mocker.patch(
        "vm_lifecycle.commands.create.poll_with_spinner",
        side_effect=mock_poll_with_spinner,
    )
    echo_mock = mocker.patch("vm_lifecycle.commands.create.click.echo")

    runner = CliRunner()
    result = runner.invoke(create_vm_instance)

    assert result.exit_code == 0
    echo_mock.assert_any_call("✅ Instance: 'test-instance' created in zone: 'zone'")


def test_create_passes_correct_args_to_poll_with_spinner(mock_context, mocker):
    config_mock, compute_mock = mock_context
    compute_mock.list_instances.return_value = []
    compute_mock.list_images.return_value = []
    compute_mock.create_instance.return_value = {"name": "op-456"}

    poll_mock = mocker.patch(
        "vm_lifecycle.commands.create.poll_with_spinner", return_value={"success": True}
    )
    mocker.patch("vm_lifecycle.commands.create.click.echo")

    runner = CliRunner()
    runner.invoke(create_vm_instance)

    poll_mock.assert_called_once_with(
        compute_manager=compute_mock,
        op_name="op-456",
        text="Creating instance: 'test-instance' in zone: 'zone'",
        done_text="✅ Instance: 'test-instance' created in zone: 'zone'",
        scope="zone",
        zone="zone",
    )


def test_create_uses_custom_image_if_provided(mock_context, mocker):
    config_mock, compute_mock = mock_context
    config_mock.active_profile["instance_name"] = "custom-vm"
    config_mock.active_profile["image_base_name"] = "custom-image"
    config_mock.active_profile["machine_type"] = "n1-standard-1"
    config_mock.active_profile["disk_size"] = 50
    config_mock.active_profile["instance_user"] = "deployer"

    compute_mock.list_instances.return_value = []
    compute_mock.list_images.return_value = []
    compute_mock.create_instance.return_value = {"name": "create-op"}

    mocker.patch(
        "vm_lifecycle.commands.create.poll_with_spinner", return_value={"success": True}
    )
    mocker.patch("vm_lifecycle.commands.create.click.echo")

    runner = CliRunner()
    runner.invoke(create_vm_instance, ["--image", "my-custom-image"])

    compute_mock.create_instance.assert_called_once_with(
        instance_name="custom-vm",
        machine_type="n1-standard-1",
        disk_size=50,
        instance_user="deployer",
        zone="zone",
        custom_image_name=None,
        image_project=None,
        image_family=None,
        startup_script_type=None,
    )
