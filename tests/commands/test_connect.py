import pytest
from click.testing import CliRunner
from subprocess import CompletedProcess
from vm_lifecycle.commands.connect import vscode_connect
import copy


@pytest.fixture
def mock_context(mocker):
    config = mocker.Mock()
    config.active_profile = copy.deepcopy(
        {
            "instance_name": "test-vm",
            "project_id": "test-project",
            "instance_user": "test-user",
        }
    )
    compute = mocker.Mock()
    zone = "europe-west1-b"
    return config, compute, zone


def test_exit_when_no_config(mocker):
    mocker.patch(
        "vm_lifecycle.commands.connect.init_gcp_context",
        return_value=(None, None, None),
    )
    result = CliRunner().invoke(vscode_connect)
    assert result.exit_code == 1


def test_instance_not_found(mocker, mock_context):
    config, compute, zone = mock_context
    mocker.patch(
        "vm_lifecycle.commands.connect.init_gcp_context",
        return_value=(config, compute, zone),
    )
    compute.get_instance_status.side_effect = ValueError("Instance not found in zone")
    result = CliRunner().invoke(vscode_connect)
    assert result.exit_code == 1
    assert "not found in zone" in result.output


def test_instance_terminated(mocker, mock_context):
    config, compute, zone = mock_context
    mocker.patch(
        "vm_lifecycle.commands.connect.init_gcp_context",
        return_value=(config, compute, zone),
    )
    compute.get_instance_status.return_value = "TERMINATED"
    result = CliRunner().invoke(vscode_connect)
    assert result.exit_code == 1
    assert "but not running" in result.output


def test_successful_connection_with_default_path(mocker, mock_context):
    config, compute, zone = mock_context
    mocker.patch(
        "vm_lifecycle.commands.connect.init_gcp_context",
        return_value=(config, compute, zone),
    )
    compute.get_instance_status.return_value = "RUNNING"

    mocker.patch("vm_lifecycle.commands.connect.create_vm_ssh_connection")

    mock_subprocess = mocker.patch("vm_lifecycle.commands.connect.subprocess.run")
    mock_subprocess.return_value = CompletedProcess(
        args=["code"], returncode=0, stdout="OK", stderr=""
    )

    result = CliRunner().invoke(vscode_connect)

    assert result.exit_code == 0
    expected_uri = (
        "vscode-remote://ssh-remote+test-vm.europe-west1-b.test-project/home/test-user"
    )
    mock_subprocess.assert_called_once_with(["code", "--folder-uri", expected_uri])


def test_successful_connection_with_custom_path(mocker, mock_context):
    config, compute, zone = mock_context
    mocker.patch(
        "vm_lifecycle.commands.connect.init_gcp_context",
        return_value=(config, compute, zone),
    )
    compute.get_instance_status.return_value = "RUNNING"

    mocker.patch("vm_lifecycle.commands.connect.create_vm_ssh_connection")

    mock_subprocess = mocker.patch("vm_lifecycle.commands.connect.subprocess.run")
    mock_subprocess.return_value = CompletedProcess(
        args=["code"], returncode=0, stdout="OK", stderr=""
    )

    custom_path = "/my/code"
    result = CliRunner().invoke(vscode_connect, ["--path", custom_path])

    assert result.exit_code == 0
    expected_uri = (
        "vscode-remote://ssh-remote+test-vm.europe-west1-b.test-project/my/code"
    )
    mock_subprocess.assert_called_once_with(["code", "--folder-uri", expected_uri])
