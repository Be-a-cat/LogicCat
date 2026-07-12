from nodes.node_base import BaseNode
from nodes.registry import registry_node
from nodes.widget import DoubleArrowSpinBox, ComboBox, DoubleArrowComBoBox
from nodes.helpers import add_metadata_to_pil

from custom_nodes.Stable_Diffusion.core import load_sd_model, generate_image

from utils.config_manager import global_config

import os
import glob
import random


@registry_node("Checkpoint加载器", "AI/SD")
class CheckpointLoadNode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": "Checkpoint Load", "node_type": "other", "size": (250, 0), "zoom_limit": "H"}
        super().__init__(conf, parent)

        self.output_pipe = self.add_output_socket("pipe", "pipe")

        self.combobox_model = ComboBox("model")
        models = self.get_models()
        self.combobox_model.addItems(models)

        self.add_widget(self.combobox_model)
        self.init()

    def logic(self):
        selected_model = self.combobox_model.currentText()
        self.inputs.update({"selected_model": selected_model})

        if not selected_model:
            return

        model_path = os.path.join(global_config.get("paths", "dirs", "sd_models"), selected_model)
        print(model_path)
        self.log(f"开始加载模型{selected_model}")
        pipe = self.run_async_task(load_sd_model, model_path)

        self.set_output_val("pipe", pipe)
        super().logic()

    @staticmethod
    def get_models():
        if not os.path.exists(global_config.get_plugin_config("Stable_Diffusion", "models_path", [])):
            return []
        model_path = global_config.get_plugin_config("Stable_Diffusion", "models_path", [])
        files = glob.glob(os.path.join(model_path, "*.safetensors"))
        return [os.path.basename(f) for f in files]

    def get_widget_input(self):
        model = self.combobox_model.currentText()
        return {"model": model}

    def set_widget_input(self, inputs):
        self.combobox_model.setCurrentText(inputs.get("model", "None"))


@registry_node("K采样器", "AI/SD")
class KSamplerNode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": "KSampler", "node_type": "other", "size": (350, 50), "zoom_limit": "H"}
        super().__init__(conf, parent)
        self.add_exec_socket()

        self.add_input_socket("pipe", "pipe", required=True)
        self.add_input_socket("positive", "string", required=True)
        self.add_input_socket("negative", "string", required=True)

        self.add_output_socket("image", "image")

        self.spin_width = DoubleArrowSpinBox("width", 1024, data_type="int")
        self.spin_height = DoubleArrowSpinBox("height", 1024, data_type="int")

        self.spin_seed = DoubleArrowSpinBox("seed", random.randint(1, 10000000000000000), data_type="int")

        self.combo_seed_mode = DoubleArrowComBoBox("seed_mode", background="#545454")
        seed_modes = ["fixed", "randomize", "increment", "decrement"]
        self.combo_seed_mode.add_items(seed_modes)
        self.combo_seed_mode.set_current_text("randomize")

        self.spin_steps = DoubleArrowSpinBox("steps", 25, data_type="int")
        self.spin_cfg = DoubleArrowSpinBox("cfg", 5.0, decimals=1)

        self.combo_sampler_name = DoubleArrowComBoBox("sampler_name", background="#545454")
        sampler_names = ["euler", "euler_ancestral", "dpmpp_2m", "dpmpp_2m_sde", "heun", "lms"]
        self.combo_sampler_name.add_items(sampler_names)
        self.combo_sampler_name.set_current_text("euler_ancestral")

        self.combo_scheduler = DoubleArrowComBoBox("scheduler", background="#545454")
        schedulers = ["normal", "karras", "exponential", "sgm_uniform", "linear"]
        self.combo_scheduler.add_items(schedulers)
        self.combo_scheduler.set_current_text("karras")

        self.add_widget(self.spin_width, "value")
        self.add_widget(self.spin_height, "value")
        self.add_widget(self.spin_seed, "value")
        self.add_widget(self.combo_seed_mode)
        self.add_widget(self.spin_steps, "value")
        self.add_widget(self.spin_cfg, "value")
        self.add_widget(self.combo_sampler_name)
        self.add_widget(self.combo_scheduler)

        self.init()

    def logic(self):
        pipe = self.get_input_val("pipe")
        if pipe is None:
            self.log("模型缺失")
            return

        positive = self.get_input_val("positive")
        negative = self.get_input_val("negative")

        width = self.spin_width.value() if self.get_input_val(0) is None else self.get_input_val(0)
        height = self.spin_height.value() if self.get_input_val(1) is None else self.get_input_val(1)
        seed = self.spin_seed.value() if self.get_input_val(2) is None else self.get_input_val(2)
        steps = self.spin_steps.value() if self.get_input_val(4) is None else self.get_input_val(4)
        cfg = self.spin_cfg.value() if self.get_input_val(5) is None else self.get_input_val(5)

        sampler_name = self.combo_sampler_name.value()
        scheduler = self.combo_scheduler.value()

        self.inputs.update({
            "positive": positive,
            "negative": negative,
            "width": width,
            "height": height,
            "seed": seed,
            "steps": steps,
            "cfg": cfg,
            "sampler_name": sampler_name,
            "scheduler": scheduler
        })

        self.log("开始生成图像!")
        image = self.run_async_task(generate_image, pipe, positive, negative, width, height, steps, cfg, seed, sampler_name, scheduler)

        if image:
            metadata = {
                "positive": positive,
                "negative": negative,
                "params": "\n".join(f"{key}: {value}" for key, value in {"width": width, "height": height, "seed": seed, "steps": steps, "cfg": cfg, "sampler_name": sampler_name, "scheduler": scheduler}.items())
            }
            image = add_metadata_to_pil(image, metadata)
            self.set_output_val("image", image)
            self.log("图像生成完毕")

    def get_widget_input(self):
        width = self.spin_width.value()
        height = self.spin_height.value()

        seed = self.spin_seed.value()
        seed_mode = self.combo_seed_mode.value()

        steps = self.spin_steps.value()
        cfg = self.spin_cfg.value()

        sampler_name = self.combo_sampler_name.value()
        scheduler = self.combo_scheduler.value()

        return {"width": width, "height": height, "seed": seed, "seed_mode": seed_mode, "steps": steps, "cfg": cfg, "sampler_name": sampler_name, "scheduler": scheduler}

    def set_widget_input(self, inputs):
        self.spin_width.set_value(inputs.get("width", 1024))
        self.spin_height.set_value(inputs.get("height", 1024))

        self.spin_seed.set_value(inputs.get("seed", 1010101010101010))
        self.combo_seed_mode.set_current_text(inputs.get("seed_mode", "randomize"))
        self.spin_steps.set_value(inputs.get("steps", 25))
        self.spin_cfg.set_value(inputs.get("cfg", 5.0))

        self.combo_sampler_name.set_current_text(inputs.get("sampler_name", "euler_ancestral"))
        self.combo_scheduler.set_current_text(inputs.get("scheduler", "karras"))

    def pre_execute(self, data=None):
        seed_mode = self.combo_seed_mode.value()
        if seed_mode == "randomize":
            seed = random.randint(1, 10000000000000000)
        elif seed_mode == "increment":
            seed = self.spin_seed.value() + 1
        elif seed_mode == "decrement":
            seed = self.spin_seed.value() - 1
        else:
            seed = self.spin_seed.value()
        self.spin_seed.set_value(seed)
