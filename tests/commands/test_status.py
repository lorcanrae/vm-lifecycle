import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from vm_lifecycle.commands.status import gcp_vm_instance_status


@pytest.fixture
def runner():
    return CliRunner()


def test_status_runs_gcloud_list_with_correct_project_id(runner):
    """Should call gcloud with correct project ID when config is valid"""
    mock_config_manager = MagicMock()
    mock_config_manager.active_profile = {"project_id": "test-project"}

    with (
        patch("vm_lifecycle.commands.status.init_gcp_context") as mock_init,
        patch("vm_lifecycle.commands.status.subprocess.run") as mock_run,
    ):
        mock_init.return_value = (mock_config_manager, MagicMock(), "europe-west1-b")

        result = runner.invoke(gcp_vm_instance_status)

        mock_run.assert_called_once_with(
            [
                "gcloud",
                "compute",
                "instances",
                "list",
                "--project=test-project",
            ]
        )
        assert result.exit_code == 0


def test_status_exits_if_no_config_manager(runner):
    """Should exit with code 1 if config_manager is None"""
    with patch("vm_lifecycle.commands.status.init_gcp_context") as mock_init:
        mock_init.return_value = (None, None, None)

        result = runner.invoke(gcp_vm_instance_status)

        assert result.exit_code == 1


def test_status_command_cli_entrypoint_runs(runner):
    """Should run CLI status command successfully end-to-end (mocked)"""
    mock_config_manager = MagicMock()
    mock_config_manager.active_profile = {"project_id": "demo-project"}

    with (
        patch("vm_lifecycle.commands.status.init_gcp_context") as mock_init,
        patch("vm_lifecycle.commands.status.subprocess.run") as mock_run,
    ):
        mock_init.return_value = (mock_config_manager, MagicMock(), "us-central1-a")
        mock_run.return_value = MagicMock()

        result = runner.invoke(gcp_vm_instance_status)

        assert result.exit_code == 0
        mock_run.assert_called_once()
