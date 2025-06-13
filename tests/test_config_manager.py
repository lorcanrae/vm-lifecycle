import pytest
from vm_lifecycle.config_manager import ConfigManager
import copy


@pytest.fixture
def temp_config_path(tmp_path):
    return tmp_path / "config.yaml"


@pytest.fixture
def config_data():
    return lambda: copy.deepcopy(
        {
            "disk_size": 100,
            "image_base_name": "vm-image",
            "instance_name": "vm1",
            "instance_user": "user1",
            "machine_type": "e2-standard-4",
            "project_id": "test-project",
            "region": "europe-west1",
            "zone": "europe-west1-b",
            "api_cache": False,
        }
    )


def test_add_and_get_profile(temp_config_path, config_data):
    config_data = config_data()
    manager = ConfigManager(config_path=temp_config_path)
    result = manager.add_profile("test_profile", config_data)
    assert result is True
    assert "test_profile" in manager.list_profiles()
    assert manager.get_active_profile() == "test_profile"
    assert manager.active == "test_profile"
    for k, v in config_data.items():
        assert manager.active_profile[k] == v
    assert manager.active_profile is not config_data


def test_add_profile_no_overwrite_should_fail(temp_config_path, config_data):
    config_data = config_data()
    manager = ConfigManager(config_path=temp_config_path)
    manager.add_profile("test_profile", config_data)
    config_data["zone"] = "europe-west2-b"
    result = manager.add_profile("test_profile", config_data, overwrite=False)
    assert result is False
    assert manager.config["test_profile"]["zone"] == "europe-west1-b"


def test_delete_nonexistent_profile_should_return_false(temp_config_path):
    manager = ConfigManager(config_path=temp_config_path)
    result = manager.delete_profile("non-existant")
    assert result is False


def test_overwrite_profile(temp_config_path, config_data):
    config_data = config_data()
    manager = ConfigManager(config_path=temp_config_path)
    manager.add_profile("test_profile", config_data)
    config_data["machine_type"] = "n1-standard-2"
    result = manager.add_profile("test_profile", config_data, overwrite=True)
    assert result is True
    assert manager.config["test_profile"]["machine_type"] == "n1-standard-2"


def test_set_active_profile(temp_config_path, config_data):
    config_data = config_data()
    manager = ConfigManager(config_path=temp_config_path)
    manager.add_profile("test_profile", config_data)
    manager.add_profile("other", config_data)
    result = manager.set_active_profile("other")
    assert result is True
    assert manager.get_active_profile() == "other"
    assert manager.active == "other"


def test_set_invalid_active_profile(temp_config_path, config_data):
    config_data = config_data()
    manager = ConfigManager(config_path=temp_config_path)
    manager.add_profile("test_profile", config_data)
    result = manager.set_active_profile("non-existent")
    assert result is False
    assert manager.get_active_profile() == "test_profile"


def test_delete_profile(temp_config_path, config_data):
    config_data = config_data()
    manager = ConfigManager(config_path=temp_config_path)
    manager.add_profile("test_profile", config_data)
    assert manager.delete_profile("test_profile") is True
    assert "test_profile" not in manager.list_profiles()


def test_update_active_zone_region(temp_config_path, config_data):
    config_data = config_data()
    manager = ConfigManager(config_path=temp_config_path)
    manager.add_profile("test_profile", config_data)
    result = manager.update_active_zone_region(op_success=True, zone="europe-west1-c")
    assert result is True
    assert manager.config["test_profile"]["zone"] == "europe-west1-c"
    assert manager.config["test_profile"]["region"] == "europe-west1"
    assert manager.active_profile["zone"] == "europe-west1-c"
    assert manager.active_profile["region"] == "europe-west1"
    assert manager.active_profile is not config_data


def test_update_active_zone_region_same_zone_should_not_update(
    temp_config_path, config_data
):
    config_data = config_data()
    manager = ConfigManager(config_path=temp_config_path)
    manager.add_profile("test_profile", config_data)
    result = manager.update_active_zone_region(op_success=True, zone="europe-west1-b")
    assert result is False


def test_delete_all_profiles(temp_config_path, config_data):
    config_data = config_data()
    manager = ConfigManager(config_path=temp_config_path)
    manager.add_profile("test_profile", config_data)
    manager.add_profile("other_profile", config_data)
    manager.delete_all_profiles()
    assert manager.config == {}
    assert manager.list_profiles() == {}


def test_list_profiles_excludes_active(temp_config_path, config_data):
    config_data = config_data()
    manager = ConfigManager(config_path=temp_config_path)
    manager.add_profile("test_profile", config_data)
    profiles = manager.list_profiles()
    assert "active" not in profiles
    assert "test_profile" in profiles


def test_pre_run_profile_check_valid(temp_config_path, config_data):
    config_data = config_data()
    manager = ConfigManager(config_path=temp_config_path)
    manager.add_profile("test_profile", config_data)
    assert manager.pre_run_profile_check() is True


def test_pre_run_profile_check_invalid(temp_config_path):
    incomplete_profile = {"project_id": "only-one-field"}
    manager = ConfigManager(config_path=temp_config_path)
    manager.add_profile("test_profile", incomplete_profile)
    assert manager.pre_run_profile_check() is False
