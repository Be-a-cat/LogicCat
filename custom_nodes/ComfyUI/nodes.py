from nodes.node_base import BaseNode
from nodes.registry import registry_node
from nodes.widget import DoubleArrowSpinBox, ComboBox, DoubleArrowComBoBox, LineEdit
from nodes.helpers import add_metadata_to_pil

from custom_nodes.ComfyUI.core import comfy_manager, t2i_workflow
from utils.config_manager import global_config

import os
import glob
import random


@registry_node("T2I", "AI/ComfyUI")
class T2INode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": "ComfyUI-T2I", "node_type": "other", "size": (350, 50), "zoom_limit": "H"}
        super().__init__(conf, parent)
        self.add_exec_socket()

        self.add_output_socket("image", "image")

        self.combo_ckpt_name = ComboBox("ckpt_name", background="#545454")
        model_list = self.get_models()
        self.combo_ckpt_name.addItems(model_list)

        self.text_edit_positive = LineEdit("positive", background="#545454")
        self.text_edit_negative = LineEdit("negative", background="#545454")

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
        sampler_list = [
            "euler",
            "euler_cfg_pp",
            "euler_ancestral",
            "euler_ancestral_cfg_pp",
            "heun",
            "heunpp2",
            "dpm_2",
            "dpm_2_ancestral",
            "lms",
            "dpm_fast",
            "dpm_adaptive",
            "dpmpp_2s_ancestral",
            "dpmpp_2s_ancestral_cfg_pp",
            "dpmpp_sde",
            "dpmpp_sde_gpu",
            "dpmpp_2m",
            "dpmpp_2m_cfg_pp",
            "dpmpp_2m_sde",
            "dpmpp_2m_sde_gpu",
            "dpmpp_3m_sde",
            "dpmpp_3m_sde_gpu",
            "ddpm",
            "LCM",
            "ipndm",
            "ipndm_v",
            "deis",
            "ddim",
            "uni_pc",
            "uni_pc_bh2"
        ]
        self.combo_sampler_name.add_items(sampler_list)
        self.combo_sampler_name.set_current_text("euler_ancestral")

        self.combo_scheduler = DoubleArrowComBoBox("scheduler", background="#545454")
        scheduler_list = [
            "normal",
            "karras",
            "exponential",
            "sgm_uniform",
            "simple",
            "ddim_uniform",
            "beta",
            "linear_quadratic"
        ]
        self.combo_scheduler.add_items(scheduler_list)
        self.combo_scheduler.set_current_text("karras")

        self.add_widget(self.combo_ckpt_name)
        self.add_widget(self.text_edit_positive, "string")
        self.add_widget(self.text_edit_negative, "string")
        self.add_widget(self.spin_width, "value")
        self.add_widget(self.spin_height, "value")
        self.add_widget(self.spin_seed, "value")
        self.add_widget(self.spin_steps, "value")
        self.add_widget(self.combo_seed_mode)
        self.add_widget(self.spin_cfg, "value")
        self.add_widget(self.combo_sampler_name)
        self.add_widget(self.combo_scheduler)

        self.init()

    @staticmethod
    def get_models():
        if not os.path.exists(global_config.get_plugin_config("ComfyUI", "models_path", [])):
            return []
        root_path = global_config.get_plugin_config("ComfyUI", "models_path", [])
        model_path = os.path.join(root_path, "checkpoints")
        files = glob.glob(os.path.join(model_path, "*.safetensors"))
        return [os.path.basename(f) for f in files]

    def logic(self):
        ckpt_name = self.combo_ckpt_name.value()
        positive = self.text_edit_positive.value() if self.get_input_val(1) is None else self.get_input_val(1)
        negative = self.text_edit_negative.value() if self.get_input_val(2) is None else self.get_input_val(2)
        width = self.spin_width.value() if self.get_input_val(3) is None else self.get_input_val(3)
        height = self.spin_height.value() if self.get_input_val(4) is None else self.get_input_val(4)
        seed = self.spin_seed.value() if self.get_input_val(5) is None else self.get_input_val(5)
        steps = self.spin_steps.value() if self.get_input_val(6) is None else self.get_input_val(6)
        cfg = self.spin_cfg.value() if self.get_input_val(8) is None else self.get_input_val(8)
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

        workflow = t2i_workflow(ckpt_name, positive, negative, width, height, seed, steps, cfg, sampler_name, scheduler)

        image = self.run_async_task(comfy_manager.generate_image_with_comfy, workflow)

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
        ckpt_name = self.combo_ckpt_name.value()

        positive = self.text_edit_positive.value()
        negative = self.text_edit_negative.value()

        width = self.spin_width.value()
        height = self.spin_height.value()

        seed = self.spin_seed.value()
        seed_mode = self.combo_seed_mode.value()

        steps = self.spin_steps.value()
        cfg = self.spin_cfg.value()

        sampler_name = self.combo_sampler_name.value()
        scheduler = self.combo_scheduler.value()

        return {"ckpt_name": ckpt_name, "positive": positive, "negative": negative, "width": width, "height": height, "seed": seed, "seed_mode": seed_mode, "steps": steps, "cfg": cfg, "sampler_name": sampler_name, "scheduler": scheduler}

    def set_widget_input(self, inputs):
        self.combo_ckpt_name.set_value(inputs.get("ckpt_name", ""))

        self.text_edit_positive.set_value(inputs.get("positive", ""))
        self.text_edit_negative.set_value(inputs.get("negative", ""))

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
