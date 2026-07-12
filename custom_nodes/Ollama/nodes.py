from nodes.node_base import BaseNode
from nodes.registry import registry_node
from nodes.widget import ComboBox, LineEdit

import requests
import ollama


@registry_node("Ollama", "AI/Ollama")
class OllamaNode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": "Ollama", "node_type": "other", "size": (200, 0), "zoom_limit": "H"}
        super().__init__(conf, parent)

        self.add_exec_socket()

        self.output_result = self.add_output_socket("result", "string")

        self.combobox_model = ComboBox("model")

        models = self.get_models()
        self.combobox_model.addItems(models)

        self.combobox_seed = ComboBox("seed")
        seed = ["randomize", "increment"]
        self.combobox_seed.addItems(seed)

        self.line_edit_system = LineEdit("system", background="#545454")
        self.line_edit_prompt = LineEdit("prompt", background="#545454", required=True)

        self.add_widget(self.combobox_model)
        self.add_widget(self.combobox_seed)
        self.add_widget(self.line_edit_system, "string")
        self.add_widget(self.line_edit_prompt, "string")

        self.init()

    @staticmethod
    def get_models():
        try:
            response = ollama.list()
            models = [model["model"] for model in response["models"]]
            return models
        except Exception:
            return []

    @staticmethod
    def execute(model, system, prompt):
        url = "http://localhost:11434/api/generate"
        data = {"model": model,
                "system": system,
                "prompt": prompt,
                "stream": False
                }
        response = requests.post(url, json=data, timeout=300)
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            return f"Error: {response.status_code}"

    def logic(self):
        model = self.combobox_model.currentText()
        seed = self.combobox_seed.currentText()
        system = self.line_edit_system.text() if self.get_input_val(2) is None else self.get_input_val(2)
        prompt = self.line_edit_prompt.text() if self.get_input_val(3) is None else self.get_input_val(3)
        self.inputs.update({"model": model, "seed": seed, "system": system, "prompt": prompt})

        if model and prompt:
            self.log("开始推理···")
            result = self.run_async_task(self.execute, model, system, prompt)
        else:
            self.log("缺少必要参数:prompt")
            return None

        self.set_output_val("result", result)

        super().logic()

    def get_widget_input(self):
        model = self.combobox_model.currentText()
        seed = self.combobox_seed.currentText()
        system = self.line_edit_system.text()
        prompt = self.line_edit_prompt.text()

        return {"model": model, "seed": seed, "system": system, "prompt": prompt}

    def set_widget_input(self, inputs):
        self.combobox_model.setCurrentText(inputs.get("model", "None"))
        self.combobox_seed.setCurrentText(inputs.get("seed", "randomize"))
        self.line_edit_system.setText(inputs.get("system", ""))
        self.line_edit_prompt.setText(inputs.get("prompt", ""))

        seed = self.combobox_seed.currentText()

        if seed == "randomize":
            self.always_update = True
        elif seed == "increment":
            self.always_update = False
