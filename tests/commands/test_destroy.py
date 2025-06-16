import pytest
from click.testing import CliRunner
from vm_lifecycle.commands.destroy import destroy_vm_instance


@pytest.fixture
def mock_context(mocker):
    config_mock = mocker.Mock()
    compute_mock = mocker.Mock()
    config_mock.active = "dev"
    config_mock.config = {
        "dev": {
            "project_id": "test-project",
            "zone": "europe-west1-b",
            "instance_name": "test-vm",
            "region": "europe-west1",
        },
        "staging": {"region": "europe-west1"},
        "active": "dev",
    }

    config_mock.active_profile = config_mock.config["dev"]
    mocker.patch(
        "vm_lifecycle.commands.destroy.init_gcp_context",
        return_value=(config_mock, compute_mock, "europe-west1-b"),
    )
    return config_mock, compute_mock


def test_destroy_exit_if_init_context_fails(mocker):
    mocker.patch(
        "vm_lifecycle.commands.destroy.init_gcp_context",
        return_value=(None, None, None),
    )
    runner = CliRunner()
    result = runner.invoke(destroy_vm_instance)
    assert result.exit_code == 1


def test_destroy_single_instance_confirmed(mock_context, mocker):
    config_mock, compute_mock = mock_context
    compute_mock.list_instances.side_effect = lambda *args, **kwargs: [
        {"name": "test-vm", "status": "RUNNING"}
    ]
    compute_mock.delete_instance.return_value = {"name": "op-destroy"}
    mocker.patch("vm_lifecycle.commands.destroy.click.confirm", return_value=True)
    spinner = mocker.patch("vm_lifecycle.commands.destroy.poll_with_spinner")
    spinner.return_value = {"success": True}

    runner = CliRunner()
    result = runner.invoke(destroy_vm_instance)
    # assert spinner.called
    assert result.exit_code == 0


def test_destroy_single_instance_aborted(mock_context, mocker):
    config_mock, compute_mock = mock_context
    compute_mock.list_instances.side_effect = lambda *args, **kwargs: [
        {"name": "test-vm", "status": "RUNNING"}
    ]
    mocker.patch("vm_lifecycle.commands.destroy.click.confirm", return_value=False)

    runner = CliRunner()
    result = runner.invoke(destroy_vm_instance)
    assert "Aborted" in result.output
    assert result.exit_code == 1


def test_destroy_all_vms_confirmed_twice(mock_context, mocker):
    config_mock, compute_mock = mock_context

    compute_mock._list_zones.return_value = ["europe-west1-b", "europe-west1-c"]

    def mock_list_instances(zone=None):
        return {
            "europe-west1-b": [{"name": "vm-1", "status": "RUNNING"}],
            "europe-west1-c": [{"name": "vm-2", "status": "RUNNING"}],
        }.get(zone, [])

    compute_mock.list_instances.side_effect = mock_list_instances

    compute_mock.delete_instance.side_effect = lambda **kwargs: {
        "name": f"op-{kwargs['instance_name']}"
    }

    mocker.patch("vm_lifecycle.commands.destroy.click.confirm", return_value=True)
    mocker.patch(
        "vm_lifecycle.commands.destroy.select_from_list",
        return_value="all instances",
    )
    spinner = mocker.patch("vm_lifecycle.commands.destroy.poll_with_spinner")
    spinner.return_value = {"success": True}

    runner = CliRunner()
    _ = runner.invoke(destroy_vm_instance, ["--vm"])

    assert spinner.call_count == 2
    spinner_texts = [str(call) for call in spinner.call_args_list]
    assert any("Destroying VM instance: vm-1" in text for text in spinner_texts)
    assert any("Destroying VM instance: vm-2" in text for text in spinner_texts)


def test_destroy_all_vms_aborted_on_first_confirm(mock_context, mocker):
    config_mock, compute_mock = mock_context

    compute_mock._list_zones.return_value = ["europe-west1-b", "europe-west1-c"]

    def mock_list_instances(zone=None):
        return {
            "europe-west1-b": [{"name": "vm-1", "status": "RUNNING"}],
            "europe-west1-c": [{"name": "vm-2", "status": "RUNNING"}],
        }.get(zone, [])

    compute_mock.list_instances.side_effect = mock_list_instances

    mocker.patch("vm_lifecycle.commands.destroy.click.confirm", return_value=False)
    mocker.patch(
        "vm_lifecycle.commands.destroy.select_from_list",
        return_value="all instances",
    )

    runner = CliRunner()
    result = runner.invoke(destroy_vm_instance, ["--vm"])

    assert "Aborted" in result.output
    assert result.exit_code == 1


def test_destroy_selected_instance_from_list(mock_context, mocker):
    config_mock, compute_mock = mock_context

    # Zone setup
    compute_mock._list_zones.return_value = ["europe-west1-b"]

    # Provide instance list for specific zone
    def mock_list_instances(zone=None):
        if zone == "europe-west1-b":
            return [{"name": "test-vm", "status": "RUNNING"}]
        return []

    compute_mock.list_instances.side_effect = mock_list_instances

    # Provide fallback list when called without zone (used by fallback path at bottom of destroy.py)
    compute_mock.list_instances.return_value = [
        {"name": "test-vm", "status": "RUNNING"}
    ]

    # Patch the user's selection to return a specific instance from the list
    mocker.patch(
        "vm_lifecycle.commands.destroy.select_from_list",
        return_value=("test-vm", "europe-west1-b"),
    )

    # Patch the delete_instance call and spinner
    compute_mock.delete_instance.return_value = {"name": "op-vm-1"}
    spinner = mocker.patch("vm_lifecycle.commands.destroy.poll_with_spinner")
    spinner.return_value = {"success": True}

    # Invoke CLI
    runner = CliRunner()
    _ = runner.invoke(destroy_vm_instance, ["--vm"])

    # Verify spinner is called with correct spinner text
    assert spinner.called
    assert any(
        call.kwargs.get("text")
        == "Destroying VM instance: 'test-vm' in zone: 'europe-west1-b'"
        for call in spinner.call_args_list
    )


def test_destroy_images_selected(mock_context, mocker):
    config_mock, compute_mock = mock_context
    compute_mock.list_images.return_value = [{"name": "image-abc"}]
    mocker.patch(
        "vm_lifecycle.commands.destroy.select_from_list", return_value="image-abc"
    )
    compute_mock.delete_image.return_value = {"name": "op-img-abc"}
    spinner = mocker.patch("vm_lifecycle.commands.destroy.poll_with_spinner")
    spinner.return_value = {"success": True}

    runner = CliRunner()
    _ = runner.invoke(destroy_vm_instance, ["--images"])
    assert "Destroying image: 'image-abc'" in str(spinner.call_args)


def test_destroy_images_all_confirmed(mock_context, mocker):
    config_mock, compute_mock = mock_context
    compute_mock.list_images.return_value = [{"name": "img1"}, {"name": "img2"}]
    mocker.patch(
        "vm_lifecycle.commands.destroy.select_from_list", return_value="all images"
    )
    mocker.patch("vm_lifecycle.commands.destroy.click.confirm", return_value=True)
    compute_mock.delete_image.side_effect = lambda name: {"name": f"op-{name}"}
    spinner = mocker.patch("vm_lifecycle.commands.destroy.poll_with_spinner")
    spinner.return_value = {"success": True}

    runner = CliRunner()
    _ = runner.invoke(destroy_vm_instance, ["--images"])
    assert spinner.call_count == 2


def test_destroy_images_aborted(mock_context, mocker):
    config_mock, compute_mock = mock_context
    compute_mock.list_images.return_value = [{"name": "img1"}, {"name": "img2"}]
    mocker.patch("vm_lifecycle.commands.destroy.select_from_list", return_value="exit")
    runner = CliRunner()
    result = runner.invoke(destroy_vm_instance, ["--images"])
    assert "Aborted" in result.output
    assert result.exit_code == 1
