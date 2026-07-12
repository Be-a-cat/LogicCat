import os
import torch
from pathlib import Path
from utils.config_manager import global_config


def check_project_integrity():
    for path in global_config.get("paths", "dirs").values():
        os.makedirs(path, exist_ok=True)

    print(torch.__version__)
    print(torch.cuda.is_available())

    print(f"PyTorch version: {torch.__version__}")

    gpu_name = torch.cuda.get_device_name(0)
    total_vram = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
    print(f"显卡型号：{gpu_name}， 显存大小：{total_vram:.2f}GB")
