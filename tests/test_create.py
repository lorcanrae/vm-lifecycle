from click.testing import CliRunner
from vm_lifecycle.commands.create import create_vm


def test_create_vm(mocker):
    runner = CliRunner()
    mock_run = mocker.patch("vm_lifecycle.commands.create.subprocess.run")

    result = runner.invoke(create_vm)

    assert result.exit_code == 0
    assert "Craeting VM" in result.output
    mock_run.assert_called_once()
