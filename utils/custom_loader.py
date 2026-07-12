import os
import sys
import importlib.util
from configs.config import DEFAULT_CONFIG
from utils.config_manager import global_config

LOADER_LOGS = []
LOADER_PLUGINS = set()


def loader_log(msg):
    print(msg)
    LOADER_LOGS.append(msg)


def load_custom_nodes():
    custom_nodes_dir = DEFAULT_CONFIG["paths"]["dirs"]["custom_nodes"]
    if not os.path.exists(custom_nodes_dir):
        os.makedirs(custom_nodes_dir, exist_ok=True)
        loader_log("未检测到到custom_nodes目录，以自动创建")
        return

    if custom_nodes_dir not in sys.path:
        sys.path.append(custom_nodes_dir)
    root_dir = DEFAULT_CONFIG["paths"]["dirs"]["root"]
    if root_dir not in sys.path:
        sys.path.append(root_dir)

    loader_log("正在扫描自定义节点文件")

    for item in sorted(os.listdir(custom_nodes_dir)):
        item_path = os.path.join(custom_nodes_dir, item)

        if item.startswith('.') or item.startswith("__"):
            continue

        if os.path.isdir(item_path):
            init_file = os.path.join(item_path, "__init__.py")
            if os.path.exists(init_file):
                module_name = f"custom_nodes.{item}"
                try:
                    spec = importlib.util.spec_from_file_location(module_name, init_file)
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)

                    plugin_name = item
                    LOADER_PLUGINS.add(plugin_name)

                    loader_log(f"成功加载自定义节点{item}")
                except ModuleNotFoundError as e:
                    missing_module = e.name
                    loader_log(f"❌ 自定义节点目录 [{item}] 缺少依赖库 [{missing_module}]，请使用 'pip install {missing_module}' 手动安装")
                except Exception as e:
                    loader_log(f"❌ 自定义节点目录 [{item}] 导入出错: {e}")
            else:
                loader_log(f"⚠️ 警告: 目录 [{item}] 缺少 __init__.py，跳过加载")

    saved_plugins = list(global_config.get_all_plugin_config().keys())

    for saved_plugin in saved_plugins:
        if saved_plugin not in LOADER_PLUGINS:
            global_config.remove_plugin_config(saved_plugin)
            loader_log(f"♻️ 发现已卸载插件的冗余配置，已自动清理: [{saved_plugin}]")
