from nodes.node_base import BaseNode
from nodes.registry import registry_node
from nodes.widget import ComboBox, LineEdit, ImageShowBox
from nodes.helpers import pil_to_base64

from utils.config_manager import global_config
from utils.buffer_pool import add_to_image_pool, get_from_image_pool

import requests
from openai import OpenAI


@registry_node("ModelScope", "AI/LLM")
class ModelScopeNode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": "ModelScope", "node_type": "other", "size": (200, 0), "zoom_limit": "HV"}
        super().__init__(conf, parent)
        self.add_exec_socket()

        self.output_result = self.add_output_socket("result", "string")

        self.conbo_model = ComboBox("model")
        self.model_dict = {
            "text_generation": ["deepseek-ai/DeepSeek-V4-Flash"],
            "visual_multimodal": ["Qwen/Qwen3.5-35B-A3B"]
        }
        models = [model for model_list in self.model_dict.values() for model in model_list]
        self.conbo_model.addItems(models)

        self.text_edit_content = LineEdit("content", background="#545454")

        self.image_box = ImageShowBox("image")
        self.image_box.resize(180, 100)

        self.add_widget(self.conbo_model)
        self.add_widget(self.text_edit_content, "string")
        self.add_widget(self.image_box, "image")

        self.init()

        self.image_id = None

    @staticmethod
    def modelscope_api(model_name, model_type, content, image):
        client = OpenAI(
            base_url='https://api-inference.modelscope.cn/v1',
            api_key=f'{global_config.get("apikey", "modelscope")}',  # ModelScope Token
        )
        messages = [{'role': 'user', 'content': f"你是谁？"}]
        if model_type == "text_generation":
            print("这是个文本生成模型")
            messages = [{'role': 'user', 'content': f"{content}"}]
        elif model_type == "visual_multimodal":
            print("这是个视觉多模态模型")
            if image:
                print("接收到了图片数据")
                image = pil_to_base64(image)
                messages = [{'role': 'user', 'content': [{'type': 'text', 'text': f'{content}'}, {'type': 'image_url', 'image_url': {'url': f"data:image/jpeg;base64,{image}"}}]}]
            else:
                print("未接收到图片数据")
                messages = [{'role': 'user', 'content': [{'type': 'text', 'text': f'{content}'}]}]

        response = client.chat.completions.create(
            model=f'{model_name}',
            messages=messages,
            stream=False
        )
        return response.choices[0].message.content

    def logic(self):
        model = self.conbo_model.value()

        model_type = ""
        if model in self.model_dict["text_generation"]:
            model_type = "text_generation"
        elif model in self.model_dict["visual_multimodal"]:
            model_type = "visual_multimodal"

        content = self.text_edit_content.value() if self.get_input_val(1) is None else self.get_input_val(1)
        image = self.get_input_val(2)

        self.inputs.update({"model": model, "model_type": model_type, "content": content, "image": image})

        result = self.run_async_task(self.modelscope_api, model, model_type, content, image)
        self.set_output_val("result", result)

    def get_widget_input(self):
        model = self.conbo_model.value()
        content = self.text_edit_content.value()
        image_id = self.image_id

        return {"model": model, "content": content, "image_id": image_id}

    def set_widget_input(self, inputs):
        self.conbo_model.setCurrentText(inputs.get("model", "None"))
        self.text_edit_content.setText(inputs.get("content", ""))
        self.image_id = inputs.get("image_id", None)
        self.image_box.set_image(get_from_image_pool(self.image_id))

    def pre_execute(self, data=None):
        image = self.get_input_val(2)
        self.image_id = add_to_image_pool(image)

        self.image_box.set_image(image)
