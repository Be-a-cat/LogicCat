import json
import subprocess
import urllib.request
import time
import os
import io
from PIL import Image
from pathlib import Path

from PySide6.QtCore import QThread, Signal


class ComfyUIThread(QThread):
    log_signal = Signal(str)

    def __init__(self, comfy_path=""):
        super().__init__()
        self.comfy_path = comfy_path
        self.process = None

    def run(self):
        base_dir = os.path.dirname(self.comfy_path)
        python_exe = os.path.join(base_dir, "python_embeded", "python.exe")

        command = [python_exe, "main.py", "--listen", "127.0.0.1", "--port", "8188"]

        creation_flags = 0x08000000 if os.name == "nt" else 0

        self.log_signal.emit("🚀 正在后台启动 ComfyUI，请稍候...\n")

        try:
            self.process = subprocess.Popen(
                command,
                cwd=self.comfy_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding="utf-8",
                errors="ignore",
                creationflags=creation_flags
            )

            while True:
                line = self.process.stdout.readline()
                if not line and self.process.poll() is not None:
                    break
                if line:
                    self.log_signal.emit(line.strip())

        except Exception as e:
            self.log_signal.emit(f"❌ 启动失败: {str(e)}")

    def stop(self):
        if self.process:
            self.log_signal.emit("\n🛑 正在关闭 ComfyUI 服务器...")
            self.process.terminate()
            self.process.wait()


class ComfyUIManager:
    def __init__(self, server_url=""):
        super().__init__()
        self.server_url = server_url

    def upload_image_to_comfy(self, image):
        """上传本地图片到 ComfyUI 的 input 文件夹，并返回文件名"""
        if isinstance(image, Image.Image):
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            image_data = buffered.getvalue()
            files = {"image": image_data}
            response = requests.post(f"{self.server_url}/upload/image", files=files)

        elif isinstance(image, str) and os.path.isfile(image):
            with open(image, "rb") as i:
                files = {"image": i}
                response = requests.post(f"{self.server_url}/upload/image", files=files)

        else:
            raise Exception(f"图片数据识别错误")

        if response.status_code == 200:
            file_info = response.json()
            print(f"上传成功！ComfyUI 识别名为: {file_info['name']}")
            return file_info['name']
        else:
            raise Exception(f"图片上传失败: {response.text}")

    def submit_queue(self, prompt_workflow):
        p = {"prompt": prompt_workflow}
        data = json.dumps(p).encode('utf-8')
        req = urllib.request.Request(f"{self.server_url}/prompt", data=data)

        response = urllib.request.urlopen(req)
        result = json.loads(response.read())
        return result['prompt_id']

    def get_history(self, prompt_id):
        """查询某个任务是否完成，并获取它的输出信息"""
        with urllib.request.urlopen(f"{self.server_url}/history/{prompt_id}") as response:
            return json.loads(response.read())

    def get_image(self, filename, subfolder, folder_type):
        """从 ComfyUI 服务器下载具体的图片数据"""
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        with urllib.request.urlopen(f"{self.server_url}/view?{url_values}") as response:
            return response.read()

    def set_server_url(self, url):
        self.server_url = url

    def generate_image_with_comfy(self, workflow):
        print("正在提交任务给 ComfyUI...")
        prompt_id = self.submit_queue(workflow)
        print(f"任务提交成功！任务编号: {prompt_id}")
        print("正在等待生成（请查看 ComfyUI 的后台控制台）...")

        while True:
            history = self.get_history(prompt_id)
            if prompt_id in history:
                print("生成完毕！正在保存图片...")
                break
            else:
                time.sleep(1.5)

        history_data = history[prompt_id]

        for node_id, node_output in history_data['outputs'].items():
            if 'images' in node_output:
                for image_info in node_output['images']:

                    image_data = self.get_image(
                        image_info['filename'],
                        image_info['subfolder'],
                        image_info['type']
                    )

                    image_stream = io.BytesIO(image_data)
                    pil_image = Image.open(image_stream)

                    return pil_image

        return None


def t2i_workflow(ckpt_name, positive="", negative="", width=1024, height=1024, seed=1000000000000, steps=25, cfg=5, sampler_name="euler_ancestral", scheduler="karras"):
    print(os.path.join(Path(__file__).resolve().parent, "workflow/t2i.json"))
    with open(os.path.join(Path(__file__).resolve().parent, "workflow/t2i.json"), "r", encoding="utf-8") as f:
        workflow = json.load(f)

    workflow["4"]["inputs"]["ckpt_name"] = ckpt_name

    workflow["3"]["inputs"]["seed"] = seed
    workflow["3"]["inputs"]["steps"] = steps
    workflow["3"]["inputs"]["cfg"] = cfg
    workflow["3"]["inputs"]["sampler_name"] = sampler_name
    workflow["3"]["inputs"]["scheduler"] = scheduler

    workflow["5"]["inputs"]["width"] = width
    workflow["5"]["inputs"]["height"] = height

    workflow["6"]["inputs"]["text"] = positive
    workflow["7"]["inputs"]["text"] = negative

    return workflow


def i2i_workflow(ckpt_name, image, positive="", negative="", width=1024, height=1024, seed=1000000000000, steps=25, cfg=5, sampler_name="euler_ancestral", scheduler="karras"):
    with open("workflow/i2i.json", "r", encoding="utf-8") as f:
        workflow = json.load(f)

    workflow["4"]["inputs"]["ckpt_name"] = ckpt_name

    workflow["3"]["inputs"]["seed"] = seed
    workflow["3"]["inputs"]["steps"] = steps
    workflow["3"]["inputs"]["cfg"] = cfg
    workflow["3"]["inputs"]["sampler_name"] = sampler_name
    workflow["3"]["inputs"]["scheduler"] = scheduler

    workflow["5"]["inputs"]["width"] = width
    workflow["5"]["inputs"]["height"] = height

    workflow["6"]["inputs"]["text"] = positive
    workflow["7"]["inputs"]["text"] = negative

    workflow["10"]["inputs"]["image"] = image

    return workflow


comfy_manager = ComfyUIManager()
