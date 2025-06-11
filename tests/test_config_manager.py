import tempfile
from pathlib import Path
from vm_lifecycle.config_manager import ConfigManager


SAMPLE_PROFILE = {
    "project_id": "sample-project",
    "zone": "europe-west1-b",
    "instance_name": "my-instance",
    "instance_user": "test-user",
    "machine_type": "e2-standard-4",
    "disk_size": 100,
    "region": "europe-west1",
    "image_base_name": "my-instance-image",
}


def test_add_and_list_profiles():
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        path = Path(tmp.name)

    manager = ConfigManager(config_path=path)
    assert manager.list_profiles() == {}

    result = manager.add_profile("dev", SAMPLE_PROFILE)
    assert result is True
    assert "dev" in manager.list_profiles()
    assert manager.config["dev"]["project_id"] == "sample-project"

    path.unlink()  # Clean up


def test_set_and_get_active_profile():
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        path = Path(tmp.name)

    manager = ConfigManager(config_path=path)
    manager.add_profile("dev", SAMPLE_PROFILE)

    assert manager.get_active_profile() == "dev"  # First added profile is active

    manager.add_profile("prod", SAMPLE_PROFILE)
    assert manager.set_active_profile("prod") is True
    assert manager.get_active_profile() == "prod"

    assert manager.set_active_profile("nonexistent") is False

    path.unlink()


def test_add_profile_with_overwrite():
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        path = Path(tmp.name)

    manager = ConfigManager(config_path=path)
    manager.add_profile("dev", SAMPLE_PROFILE)

    new_profile = SAMPLE_PROFILE.copy()
    new_profile["zone"] = "us-central1-a"

    result = manager.add_profile("dev", new_profile, overwrite=False)
    assert result is False  # Should not overwrite

    result = manager.add_profile("dev", new_profile, overwrite=True)
    assert result is True
    assert manager.config["dev"]["zone"] == "us-central1-a"

    path.unlink()


def test_delete_profile():
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        path = Path(tmp.name)

    manager = ConfigManager(config_path=path)
    manager.add_profile("dev", SAMPLE_PROFILE)
    manager.add_profile("prod", SAMPLE_PROFILE)

    assert "dev" in manager.list_profiles()
    manager.delete_profile("dev")
    assert "dev" not in manager.list_profiles()

    assert manager.delete_profile("nonexistent") is False

    path.unlink()


def test_delete_all_profiles():
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        path = Path(tmp.name)

    manager = ConfigManager(config_path=path)
    manager.add_profile("dev", SAMPLE_PROFILE)
    manager.add_profile("prod", SAMPLE_PROFILE)

    assert len(manager.list_profiles()) == 2

    manager.delete_all_profiles()
    assert manager.list_profiles() == {}
    assert manager.get_active_profile() is None

    path.unlink()
