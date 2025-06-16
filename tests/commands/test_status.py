import pytest
from click.testing import CliRunner
from vm_lifecycle.commands.status import gcp_vm_instance_status


@pytest.fixture
def mock_context(mocker):
    """Provides a mocked config_manager and compute_manager"""
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
        "active": "dev",
    }
    config_mock.active_profile = config_mock.config["dev"]

    mocker.patch(
        "vm_lifecycle.commands.status.init_gcp_context",
        return_value=(config_mock, compute_mock, "europe-west1-b"),
    )
    return config_mock, compute_mock


def test_status_runs_gcloud_list_with_correct_project_id(mock_context, mocker):
    """Should call gcloud with correct project ID when config is valid"""
    config_mock, _ = mock_context
    subprocess_mock = mocker.patch("vm_lifecycle.commands.status.subprocess.run")

    runner = CliRunner()
    result = runner.invoke(gcp_vm_instance_status)

    assert result.exit_code == 0
    subprocess_mock.assert_called_once_with(
        [
            "gcloud",
            "compute",
            "instances",
            "list",
            f"--project={config_mock.active_profile['project_id']}",
        ]
    )


def test_status_exits_if_no_config_manager(mocker):
    """Should exit with code 1 if config_manager is None"""
    mocker.patch(
        "vm_lifecycle.commands.status.init_gcp_context",
        return_value=(None, None, None),
    )
    runner = CliRunner()
    result = runner.invoke(gcp_vm_instance_status)

    assert result.exit_code == 1


def test_status_command_runs_without_errors(mock_context, mocker):
    """Should run CLI command successfully (integration)"""
    mocker.patch("vm_lifecycle.commands.status.subprocess.run")
    runner = CliRunner()
    result = runner.invoke(gcp_vm_instance_status)
    assert result.exit_code == 0
