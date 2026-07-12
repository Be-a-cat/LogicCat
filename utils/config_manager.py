import os
import json
from configs.config import CONFIG_FILE, DEFAULT_CONFIG


class ConfigManager:
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)

                    for section, values in loaded.items():
                        if section in self.config:
                            self.config[section].update(values)
                        else:
                            self.config[section] = values
            except Exception as e:
                print(f"读取配置文件失败: {e}")

    def save(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def get(self, *keys):
        if len(keys) == 0:
            raise ValueError("缺失输入参数")

        result = self.config
        for key in keys:
            if isinstance(result, dict):
                result = result.get(key)
            else:
                return None
        return result

    def set(self, *keys, value):
        if len(keys) == 0:
            raise ValueError("缺失输入参数")

        current = self.config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
            if not isinstance(current, dict):
                raise TypeError(f"{key} not is a dict")

        lask_key = keys[-1]
        current[lask_key] = value
        self.save()

    def get_plugin_config(self, plugin_name, key, default=None):
        plugins_section = self.config.setdefault("plugins", {})
        plugins_section = plugins_section.setdefault(plugin_name, {})
        return plugins_section.get(key, default)

    def set_plugin_config(self, plugin_name, key, value):
        plugin_section = self.config.setdefault("plugins", {})
        plugin_section = plugin_section.setdefault(plugin_name, {})
        plugin_section[key] = value
        self.save()

    def remove_plugin_config(self, plugin_name):
        if "plugins" in self.config and plugin_name in self.config["plugins"]:
            del self.config["plugins"][plugin_name]
            self.save()

    def get_all_plugin_config(self):
        return self.config.get("plugins", {})


global_config = ConfigManager()
