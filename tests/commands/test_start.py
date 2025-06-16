import pytest
from googleapiclient.errors import HttpError
from click.testing import CliRunner

from vm_lifecycle.commands.start import start_vm_instance


@pytest.fixture
def mock_context(mocker):
    config_mock = mocker.Mock()
    compute_mock = mocker.Mock()
    config_mock.active_profile = {
        "project_id": "test-project",
        "zone": "europe-west1-b",
        "instance_name": "test-vm",
        "instance_user": "user1",
        "machine_type": "e2-standard-4",
        "disk_size": 50,
        "region": "europe-west1",
        "image_base_name": "vm-image",
        "api_cache": False,
    }
    config_mock.active = "test-profile"
    mocker.patch(
        "vm_lifecycle.commands.start.init_gcp_context",
        return_value=(config_mock, compute_mock, "europe-west1-b"),
    )
    return config_mock, compute_mock


def test_instance_already_running(mock_context, mocker):
    """Should print a message and exit early if instance is already RUNNING."""
    config_mock, compute_mock = mock_context
    compute_mock.list_instances.return_value = [
        {"name": "test-vm", "status": "RUNNING"}
    ]

    runner = CliRunner()
    result = runner.invoke(start_vm_instance)

    assert "already running" in result.output
    assert result.exit_code == 0


def test_start_instance_same_zone(mock_context, mocker):
    """Should start the VM if it exists and is TERMINATED in the same zone."""
    config_mock, compute_mock = mock_context

    # Simulate instance is found and terminated
    compute_mock.list_instances.return_value = [
        {"name": "test-vm", "status": "TERMINATED"}
    ]
    compute_mock.start_instance.return_value = {"name": "op-123"}

    # Patch poll_with_spinner to simulate printing spinner text
    def fake_spinner(**kwargs):
        print(kwargs.get("text", ""))
        return {"success": True}

    mocker.patch(
        "vm_lifecycle.commands.start.poll_with_spinner",
        side_effect=fake_spinner,
    )

    runner = CliRunner()
    result = runner.invoke(start_vm_instance)

    # This message is passed as `text=` to poll_with_spinner in the command
    assert "Starting Instance" in result.output
    compute_mock.start_instance.assert_called_once()


def test_start_instance_from_image_in_new_zone(mock_context, mocker):
    """Should create image, destroy instance, and recreate in new zone if zone differs."""
    config_mock, compute_mock = mock_context
    config_mock.active_profile["zone"] = "europe-west1-a"
    compute_mock.list_instances.return_value = [
        {"name": "test-vm", "status": "TERMINATED"}
    ]

    compute_mock.create_image_from_instance.return_value = {
        "name": "op-image",
        "targetLink": "link/img-1",
    }
    compute_mock.delete_instance.return_value = {"name": "op-delete"}
    compute_mock.get_latest_image_from_family.return_value = {"name": "img-1"}
    compute_mock.create_instance.return_value = {"name": "op-create"}

    # Patch spinner to simulate text output
    def fake_spinner(**kwargs):
        print(kwargs.get("text", ""))
        print(kwargs.get("done_text", ""))
        return {"success": True, "operation": {"targetLink": "link/img-1"}}

    mocker.patch(
        "vm_lifecycle.commands.start.poll_with_spinner",
        side_effect=fake_spinner,
    )

    runner = CliRunner()
    result = runner.invoke(start_vm_instance, ["--zone", "europe-west1-b"])

    assert "Creating image from instance" in result.output
    assert "Destroying VM instance" in result.output
    assert "created in zone" in result.output


def test_create_instance_from_image_if_no_instance(mock_context, mocker):
    """Should create instance from image if none exists."""
    config_mock, compute_mock = mock_context
    compute_mock.list_instances.return_value = []

    compute_mock.get_latest_image_from_family.return_value = {"name": "img-42"}
    compute_mock.create_instance.return_value = {"name": "op-create"}

    def fake_spinner(**kwargs):
        print(kwargs.get("text", ""))
        print(kwargs.get("done_text", ""))
        return {"success": True}

    mocker.patch(
        "vm_lifecycle.commands.start.poll_with_spinner",
        side_effect=fake_spinner,
    )

    runner = CliRunner()
    result = runner.invoke(start_vm_instance)

    assert "Creating instance from image" in result.output
    assert "created in zone" in result.output
    compute_mock.create_instance.assert_called_once()


def test_start_instance_spinner_failure(mock_context, mocker):
    """Should print error if spinner reports failure when starting instance."""
    config_mock, compute_mock = mock_context
    compute_mock.list_instances.return_value = [
        {"name": "test-vm", "status": "TERMINATED"}
    ]
    compute_mock.start_instance.return_value = {"name": "op-123"}

    mocker.patch(
        "vm_lifecycle.commands.start.poll_with_spinner",
        return_value={"success": False, "error": {"message": "start failed"}},
    )

    runner = CliRunner()
    result = runner.invoke(start_vm_instance)

    assert "start failed" in result.output
    assert result.exit_code == 1


def test_start_image_creation_failure(mock_context, mocker):
    """Should exit with error if image creation operation fails."""
    config_mock, compute_mock = mock_context
    config_mock.active_profile["zone"] = "europe-west1-a"
    compute_mock.list_instances.return_value = [
        {"name": "test-vm", "status": "TERMINATED"}
    ]

    compute_mock.create_image_from_instance.return_value = {"name": "op-image"}
    mocker.patch(
        "vm_lifecycle.commands.start.poll_with_spinner",
        return_value={"success": False, "error": {"message": "image creation failed"}},
    )

    runner = CliRunner()
    result = runner.invoke(start_vm_instance, ["--zone", "europe-west1-b"])

    assert "image creation failed" in result.output
    assert result.exit_code == 1


def test_start_no_image_from_family(mock_context, mocker):
    """Should error if no image is found for the image family."""
    config_mock, compute_mock = mock_context
    compute_mock.list_instances.return_value = []

    compute_mock.get_latest_image_from_family.return_value = None

    runner = CliRunner()
    result = runner.invoke(start_vm_instance)

    assert "No image found for family" in result.output
    assert result.exit_code == 1


def test_start_instance_with_unexpected_status(mock_context, mocker):
    """Should raise or handle unknown instance statuses gracefully."""
    config_mock, compute_mock = mock_context
    compute_mock.list_instances.return_value = [
        {"name": "test-vm", "status": "STOPPING"}
    ]

    runner = CliRunner()
    result = runner.invoke(start_vm_instance)

    assert "Unsupported status" in result.output or result.exit_code != 0


def test_start_exits_if_init_context_fails(mocker):
    """Should exit silently if init_gcp_context returns None (e.g., profile is invalid)."""
    mocker.patch(
        "vm_lifecycle.commands.start.init_gcp_context",
        return_value=(None, None, None),
    )
    runner = CliRunner()
    result = runner.invoke(start_vm_instance)
    assert result.exit_code == 0
    assert result.output.strip() == ""


def test_start_handles_no_instances_response(mock_context, mocker):
    """Should create from image if list_instances returns empty list."""
    config_mock, compute_mock = mock_context
    config_mock.active_profile["zone"] = "europe-west1-a"  # simulate zone mismatch
    compute_mock.list_instances.return_value = []

    compute_mock.get_latest_image_from_family.return_value = {"name": "img-xyz"}
    compute_mock.create_instance.return_value = {"name": "op-create"}

    def fake_spinner(**kwargs):
        print(kwargs.get("text", ""))
        print(kwargs.get("done_text", ""))
        return {"success": True, "operation": {"name": "op-create"}}

    mocker.patch(
        "vm_lifecycle.commands.start.poll_with_spinner",
        side_effect=fake_spinner,
    )

    runner = CliRunner()
    result = runner.invoke(start_vm_instance, ["--zone", "europe-west1-b"])

    assert "Creating instance from image" in result.output
    assert result.exit_code == 0


def test_start_handles_http_error_on_image_fetch(mock_context, mocker):
    """Should print and exit if get_latest_image_from_family raises HttpError."""
    from httplib2 import Response

    config_mock, compute_mock = mock_context
    compute_mock.list_instances.return_value = []

    fake_response = Response({"status": 403})
    mock_error = HttpError(resp=fake_response, content=b"Access denied")
    compute_mock.get_latest_image_from_family.side_effect = mock_error

    runner = CliRunner()
    result = runner.invoke(start_vm_instance)

    assert "❗ Error:" in result.output
    assert result.exit_code == 1
