import yaml
from pathlib import Path
from vm_lifecycle.params import DEFAULT_CONFIG_PATH


class ConfigManager:
    def __init__(self, config_path: Path = DEFAULT_CONFIG_PATH):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        if self.config_path.exists():
            with self.config_path.open("r") as f:
                return yaml.safe_load(f) or {}
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
        self.config = {"active": None}
        self.save_config()
