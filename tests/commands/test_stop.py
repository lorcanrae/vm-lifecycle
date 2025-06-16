import pytest
from click.testing import CliRunner
from vm_lifecycle.commands.stop import stop_vm_instance


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
        "vm_lifecycle.commands.stop.init_gcp_context",
        return_value=(config_mock, compute_mock, "europe-west1-b"),
    )
    return config_mock, compute_mock


def test_stop_instance_not_found(mock_context):
    config_mock, compute_mock = mock_context
    compute_mock.list_instances.return_value = []

    runner = CliRunner()
    result = runner.invoke(stop_vm_instance)

    assert "No instance named" in result.output
    assert result.exit_code == 1


def test_stop_instance_already_terminated(mock_context, mocker):
    config_mock, compute_mock = mock_context

    compute_mock.list_instances.return_value = [
        {"name": "test-vm", "status": "TERMINATED"}
    ]
    compute_mock.create_image_from_instance.return_value = {
        "name": "op-image",
        "targetLink": "link/img-123",
    }
    compute_mock.get_dangling_images.return_value = []
    compute_mock.delete_instance.return_value = {"name": "op-delete"}

    spinner = mocker.patch("vm_lifecycle.commands.stop.poll_with_spinner")
    spinner.return_value = {
        "success": True,
        "operation": {"targetLink": "link/img-123"},
    }

    runner = CliRunner()
    _ = runner.invoke(stop_vm_instance)

    spinner_texts = [call.kwargs["text"] for call in spinner.call_args_list]
    assert any("Creating image from instance" in text for text in spinner_texts)


def test_stop_instance_success(mock_context, mocker):
    config_mock, compute_mock = mock_context
    compute_mock.list_instances.return_value = [
        {"name": "test-vm", "status": "RUNNING"}
    ]
    compute_mock.stop_instance.return_value = {"name": "op-stop"}
    compute_mock.create_image_from_instance.return_value = {
        "name": "op-image",
        "targetLink": "link/img-123",
    }
    compute_mock.get_dangling_images.return_value = ["img-old"]
    compute_mock.delete_image.return_value = {"name": "op-img-del"}
    compute_mock.delete_instance.return_value = {"name": "op-delete"}

    spinner = mocker.patch("vm_lifecycle.commands.stop.poll_with_spinner")
    spinner.return_value = {
        "success": True,
        "operation": {"targetLink": "link/img-123"},
    }

    runner = CliRunner()
    _ = runner.invoke(stop_vm_instance)

    texts = [call.kwargs["text"] for call in spinner.call_args_list]
    assert any("Stopping instance" in t for t in texts)
    assert any("Creating image from instance" in t for t in texts)
    assert any("Destroying image: 'img-old'" in t for t in texts)
    assert any("Destroying VM instance" in t for t in texts)


def test_stop_instance_failure_poll(mock_context, mocker):
    config_mock, compute_mock = mock_context
    compute_mock.list_instances.return_value = [
        {"name": "test-vm", "status": "RUNNING"}
    ]
    compute_mock.stop_instance.return_value = {"name": "op-stop"}

    spinner = mocker.patch("vm_lifecycle.commands.stop.poll_with_spinner")
    spinner.return_value = {
        "success": False,
        "error": {"message": "failed to stop"},
    }

    runner = CliRunner()
    result = runner.invoke(stop_vm_instance)

    assert "failed to stop" in result.output
    assert result.exit_code == 1


def test_stop_exit_if_init_context_fails(mocker):
    mocker.patch(
        "vm_lifecycle.commands.stop.init_gcp_context", return_value=(None, None, None)
    )

    runner = CliRunner()
    result = runner.invoke(stop_vm_instance)

    assert result.exit_code == 1


def test_stop_instance_with_keep_flag(mock_context, mocker):
    config_mock, compute_mock = mock_context

    compute_mock.list_instances.return_value = [
        {"name": "test-vm", "status": "TERMINATED"}
    ]
    compute_mock.create_image_from_instance.return_value = {
        "name": "op-img",
        "targetLink": "link/image-1",
    }
    compute_mock.get_dangling_images.return_value = []
    compute_mock.delete_instance.return_value = {"name": "op-delete"}

    spinner = mocker.patch("vm_lifecycle.commands.stop.poll_with_spinner")
    spinner.return_value = {
        "success": True,
        "operation": {"targetLink": "link/image-1"},
    }

    runner = CliRunner()
    _ = runner.invoke(stop_vm_instance, ["--keep"])

    spinner_texts = [call.kwargs.get("text", "") for call in spinner.call_args_list]
    assert any("Creating image from instance" in text for text in spinner_texts)
    assert not any("Destroying VM instance" in text for text in spinner_texts)


def test_stop_instance_with_basic_flag(mock_context, mocker):
    config_mock, compute_mock = mock_context

    compute_mock.list_instances.return_value = [
        {"name": "test-vm", "status": "RUNNING"}
    ]
    compute_mock.stop_instance.return_value = {"name": "op-stop"}

    spinner = mocker.patch("vm_lifecycle.commands.stop.poll_with_spinner")
    spinner.return_value = {"success": True}

    runner = CliRunner()
    _ = runner.invoke(stop_vm_instance, ["--basic"])

    spinner_texts = [call.kwargs.get("text", "") for call in spinner.call_args_list]
    assert any("Stopping instance" in text for text in spinner_texts)
    assert not any("Creating image from instance" in text for text in spinner_texts)
    assert not any("Destroying VM instance" in text for text in spinner_texts)


def test_stop_removes_dangling_images(mock_context, mocker):
    config_mock, compute_mock = mock_context

    compute_mock.list_instances.return_value = [
        {"name": "test-vm", "status": "TERMINATED"}
    ]
    compute_mock.create_image_from_instance.return_value = {
        "name": "op-img",
        "targetLink": "link/image-1",
    }
    compute_mock.get_dangling_images.return_value = ["old-image-1", "old-image-2"]
    compute_mock.delete_image.side_effect = lambda name: {"name": f"op-{name}"}
    compute_mock.delete_instance.return_value = {"name": "op-delete"}

    spinner = mocker.patch("vm_lifecycle.commands.stop.poll_with_spinner")
    spinner.return_value = {
        "success": True,
        "operation": {"targetLink": "link/image-1"},
    }

    runner = CliRunner()
    _ = runner.invoke(stop_vm_instance)

    spinner_texts = [call.kwargs.get("text", "") for call in spinner.call_args_list]
    assert any("Destroying image: 'old-image-1'" in text for text in spinner_texts)
    assert any("Destroying image: 'old-image-2'" in text for text in spinner_texts)


def test_stop_skips_dangling_image_deletion_when_none(mock_context, mocker):
    config_mock, compute_mock = mock_context

    compute_mock.list_instances.return_value = [
        {"name": "test-vm", "status": "TERMINATED"}
    ]
    compute_mock.create_image_from_instance.return_value = {
        "name": "op-img",
        "targetLink": "link/image-1",
    }
    compute_mock.get_dangling_images.return_value = []
    compute_mock.delete_instance.return_value = {"name": "op-delete"}

    spinner = mocker.patch("vm_lifecycle.commands.stop.poll_with_spinner")
    spinner.return_value = {
        "success": True,
        "operation": {"targetLink": "link/image-1"},
    }

    runner = CliRunner()
    _ = runner.invoke(stop_vm_instance)

    spinner_texts = [call.kwargs.get("text", "") for call in spinner.call_args_list]
    assert not any("Destroying image:" in text for text in spinner_texts)


def test_stop_dangling_image_deletion_failure(mock_context, mocker):
    config_mock, compute_mock = mock_context

    compute_mock.list_instances.return_value = [
        {"name": "test-vm", "status": "TERMINATED"}
    ]
    compute_mock.create_image_from_instance.return_value = {
        "name": "op-img",
        "targetLink": "link/image-1",
    }
    compute_mock.get_dangling_images.return_value = ["old-image-fail"]
    compute_mock.delete_image.return_value = {"name": "op-fail"}
    compute_mock.delete_instance.return_value = {"name": "op-delete"}

    spinner = mocker.patch("vm_lifecycle.commands.stop.poll_with_spinner")
    spinner.side_effect = [
        {"success": True, "operation": {"targetLink": "link/image-1"}},  # image create
        {"success": False, "error": {"message": "failed to delete"}},  # delete fail
        {"success": True},  # instance delete
    ]

    runner = CliRunner()
    result = runner.invoke(stop_vm_instance)

    assert "failed to delete" in result.output or result.exit_code == 1


def test_stop_image_creation_fails(mock_context, mocker):
    config_mock, compute_mock = mock_context
    compute_mock.list_instances.return_value = [
        {"name": "test-vm", "status": "TERMINATED"}
    ]
    compute_mock.create_image_from_instance.return_value = {"name": "op-img"}

    spinner = mocker.patch("vm_lifecycle.commands.stop.poll_with_spinner")
    spinner.return_value = {
        "success": False,
        "error": {"message": "image creation failed"},
    }

    runner = CliRunner()
    result = runner.invoke(stop_vm_instance)

    # assert "image creation failed" in result.output
    assert result.exit_code == 1


def test_stop_instance_name_mismatch(mock_context):
    config_mock, compute_mock = mock_context
    compute_mock.list_instances.return_value = [
        {"name": "other-instance", "status": "RUNNING"}
    ]

    runner = CliRunner()
    result = runner.invoke(stop_vm_instance)

    assert "No instance named" in result.output or result.exit_code == 1
