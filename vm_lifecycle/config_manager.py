import yaml
from pathlib import Path
from vm_lifecycle.params import DEFAULT_CONFIG_PATH


class ConfigManager:
    REQUIRED_APIS = ["compute.googleapis.com"]

    def __init__(self, config_path: Path = DEFAULT_CONFIG_PATH):
        self.config_path = config_path
        self.config = self._load_config()
        self.active = self.config["active"] or None
        self.active_profile = self._load_active_profile()

    def _load_config(self):
        if self.config_path.exists():
            with self.config_path.open("r") as f:
                return yaml.safe_load(f) or {}
        return {}

    def _load_active_profile(self):
        if self.config:
            return self.config.get(self.active, {})
        return {}

    def save_config(self):
        with self.config_path.open("w") as f:
            yaml.dump(self.config, f)

    def list_profiles(self):
        return {k: v for k, v in self.config.items() if k != "active"}

    def get_active_profile(self):
        return self.config.get("active")

    def set_active_profile(self, profile_name):
        if profile_name in self.list_profiles():
            self.config["active"] = profile_name
            self.save_config()
            return True
        return False

    def add_profile(self, profile_name, profile_config, overwrite=False):
        if profile_name in self.config and not overwrite:
            return False
        self.config[profile_name] = profile_config
        if "active" not in self.config:
            self.config["active"] = profile_name
        self.save_config()
        return True

    def delete_profile(self, profile_name):
        if profile_name in self.config:
            del self.config[profile_name]
            self.save_config()
            return True
        return False

    def delete_all_profiles(self):
        self.config = {}
        self.save_config()

    def _validate_active_profile(self):
        # Check keys exist
        req_keys = set(
            [
                "disk_size",
                "image_base_name",
                "instance_name",
                "instance_user",
                "machine_type",
                "project_id",
                "region",
                "zone",
                "api_cache",
            ]
        )

        if set(self.active_profile.keys()) != req_keys:
            return False
        return True

    def pre_run_profile_check(self):
        if not self.active_profile or not self._validate_active_profile():
            return False
        return True

    # Pre run check? or place into GCP Manager?


if __name__ == "__main__":
    manager = ConfigManager()

    from pprint import pprint as print

    print(manager.active)
    print(manager.active_profile.keys())
    print(manager.validate_active_profile())
