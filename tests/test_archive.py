import pytest
from click.testing import CliRunner
from vm_lifecycle.commands.archive import archive_vm


def test_archive_vm(mocker):
    runner = CliRunner()

    mock_run = mocker.patch("vm_lifecycle.commands.archive.subprocess.run")

    result = runner.invoke(archive_vm)

    assert result.exit_code == 0
    assert "Archiving VM" in result.output
    mock_run.assert_called_once()
