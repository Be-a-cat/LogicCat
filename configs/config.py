import os
from pathlib import Path

CONFIG_FILE = os.path.join(Path(__file__).resolve().parent.parent, "user\\settings.json")

DEFAULT_CONFIG = {
    "paths": {
        "dirs": {
            "root": str(Path(__file__).resolve().parent.parent),
            "workflow_save": os.path.join(Path(__file__).resolve().parent.parent, "user\\workflows"),
            "llm_models": os.path.join(Path(__file__).resolve().parent.parent, "models\\LLM"),
            "sd_models": os.path.join(Path(__file__).resolve().parent.parent, "models\\SD"),
            "run_history": os.path.join(Path(__file__).resolve().parent.parent, "outputs\\runs"),
            "image_save": os.path.join(Path(__file__).resolve().parent.parent, "outputs\\images"),
            "custom_nodes": os.path.join(Path(__file__).resolve().parent.parent, "custom_nodes")
        },
        "files": {
            "default_workflow": os.path.join(Path(__file__).resolve().parent.parent, "configs\\.default.json"),
            "autosave_workflow": os.path.join(Path(__file__).resolve().parent.parent, "user\\.autosave.json")
        }
    },
    "apikey": {
        "free_chatgpt": "",
        "baidu_translate": "",
    }
}
