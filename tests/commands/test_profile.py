import pytest
from click.testing import CliRunner
from pathlib import Path
from vm_lifecycle.commands.profile import (
    create_profile,
    list_profiles,
    set_profile,
    delete_profile,
)


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_config_manager(mocker):
    mock = mocker.patch("vm_lifecycle.commands.profile.ConfigManager", autospec=True)
    instance = mock.return_value
    instance.config = {}
    instance.config_path = Path("/mock/path/config.yaml")
    instance.get_active_profile.return_value = None
    instance.list_profiles.return_value = {}
    return instance


def test_create_profile_adds_new_profile(runner, mocker, mock_config_manager):
    mocker.patch(
        "vm_lifecycle.commands.profile.prompt_validation",
        side_effect=["test-profile", "test-project", "test-instance"],
    )
    mocker.patch(
        "vm_lifecycle.commands.profile.click.prompt",
        side_effect=["europe-west1-b", "ubuntu", "e2-standard-4", 100],
    )
    mocker.patch("vm_lifecycle.commands.profile.click.confirm", return_value=False)

    result = runner.invoke(create_profile)

    assert result.exit_code == 0
    assert "✅ Profile 'test-profile' added." in result.output


def test_create_profile_overwrite_decline(runner, mocker):
    mock_cm = mocker.MagicMock()
    mock_cm.config = {"test-profile": {}}
    mock_cm.list_profiles.return_value = {"test-profile": {}}
    mock_cm.get_active_profile.return_value = None
    mock_cm.add_profile.side_effect = lambda name, cfg, overwrite=False: overwrite

    mocker.patch(
        "vm_lifecycle.commands.profile.prompt_validation",
        side_effect=["test-profile", "test-project", "test-instance"],
    )
    mocker.patch(
        "vm_lifecycle.commands.profile.click.prompt",
        side_effect=["europe-west1-b", "ubuntu", "e2-standard-4", 100],
    )
    confirm = mocker.patch(
        "vm_lifecycle.commands.profile.click.confirm", return_value=False
    )

    # ✅ Patch ConfigManager at correct location
    mocker.patch("vm_lifecycle.commands.profile.ConfigManager", return_value=mock_cm)

    result = runner.invoke(create_profile)

    print(result.output)

    assert result.exit_code == 1
    assert "❌ Aborted." in result.output
    confirm.assert_called_once()


def test_list_profiles_displays_profiles(runner, mocker):
    mock_cm = mocker.MagicMock()
    mock_cm.list_profiles.return_value = {
        "test": {"project_id": "abc", "zone": "europe-west1-b"},
    }
    mock_cm.get_active_profile.return_value = "test"
    mock_cm.config_path = Path("/mock/path/config.yaml")

    # Correctly patch ConfigManager at its usage site
    mocker.patch("vm_lifecycle.commands.profile.ConfigManager", return_value=mock_cm)

    result = runner.invoke(list_profiles)

    assert result.exit_code == 0
    assert "test" in result.output
    assert "project_id" in result.output


def test_list_profiles_empty_exits(runner, mocker, mock_config_manager):
    mock_config_manager.return_value.list_profiles.return_value = {}
    mock_config_manager.return_value.config_path = Path("/mock/path/config.yaml")

    result = runner.invoke(list_profiles)

    assert result.exit_code == 1
    assert "No profiles found" in result.output


def test_set_profile_argument_success(runner, mocker):
    mock_cm = mocker.MagicMock()
    mock_cm.list_profiles.return_value = {"test": {}}
    mock_cm.get_active_profile.return_value = "test"
    mock_cm.set_active_profile.return_value = True
    mock_cm.config_path = Path("/mock/path/config.yaml")

    # Correct patch scope
    mocker.patch("vm_lifecycle.commands.profile.ConfigManager", return_value=mock_cm)

    result = runner.invoke(set_profile, ["test"])

    assert result.exit_code == 0
    assert "✅ Active profile set to: 'test'" in result.output


def test_set_profile_argument_failure(runner, mocker):
    mock_cm = mocker.MagicMock()
    mock_cm.list_profiles.return_value = {"test": {}}  # ensure keys() works
    mock_cm.get_active_profile.return_value = "test"
    mock_cm.set_active_profile.return_value = False
    mock_cm.config_path = Path("/mock/path/config.yaml")

    # Correct patch scope
    mocker.patch("vm_lifecycle.commands.profile.ConfigManager", return_value=mock_cm)

    result = runner.invoke(set_profile, ["nonexistent"])

    assert result.exit_code == 1
    assert "❌ Profile 'nonexistent' not found." in result.output


def test_delete_profile_by_argument(runner, mocker, mock_config_manager):
    mock_config_manager.return_value.list_profiles.return_value = {"test": {}}
    mock_config_manager.return_value.delete_profile.return_value = True

    result = runner.invoke(delete_profile, ["test"])

    assert result.exit_code == 0
    assert "🗑️  Deleted profile 'test'" in result.output


def test_delete_all_profiles_confirmed(runner, mocker):
    mock_cm = mocker.MagicMock()
    # ✅ Real dict to allow .keys() to behave normally
    mock_cm.list_profiles.return_value = {"test": {"zone": "europe-west1-b"}}
    mock_cm.delete_all_profiles.return_value = None
    mock_cm.config_path = Path("/mock/path/config.yaml")

    mocker.patch("vm_lifecycle.commands.profile.ConfigManager", return_value=mock_cm)
    mocker.patch("vm_lifecycle.commands.profile.click.confirm", return_value=True)

    result = runner.invoke(delete_profile, ["--all"])

    assert result.exit_code == 0
    assert "🗑️  All profiles deleted." in result.output
