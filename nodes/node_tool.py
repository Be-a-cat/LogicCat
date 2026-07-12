from nodes.node_base import BaseNode
from nodes.registry import registry_node
from nodes.widget import ComboBox

from utils.config_manager import global_config

import requests
import hashlib
import uuid


@registry_node("百度翻译", "工具")
class BaiduTranslateNode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": "Baidu Translate", "node_type": "other", "size": (200, 0), "zoom_limit": "H"}
        super().__init__(conf, parent)
        self.add_exec_socket()

        self.input_text = self.add_input_socket("string", "string", required=True)
        self.putput_text = self.add_output_socket("string", "string")

        self.conbo_language = ComboBox("language")
        self.languages = {"中文": "zh", "英语": "en", "日语": "jp", "韩语": "kor", "法语": "fra", "俄语": "ru", "意大利语": "it", "繁体中文": "cht"}
        self.conbo_language.addItems(list(self.languages.keys()))
        self.conbo_language.setCurrentText("英语")

        self.add_widget(self.conbo_language)

        self.init()

    @staticmethod
    def baidu_translate(appid, secret_key, query, from_lang='auto', to_lang='en'):
        # 请替换为您的API密钥信息
        appid = appid
        secret_key = secret_key

        # 生成签名所需的唯一随机数（salt）
        salt = str(uuid.uuid1())

        # 拼接签名字符串，并进行MD5加密
        sign_str = appid + query + salt + secret_key
        sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()

        # 构造请求URL及参数
        url = 'https://fanyi-api.baidu.com/api/trans/vip/translate'
        params = {
            'q': query,
            'from': from_lang,
            'to': to_lang,
            'appid': appid,
            'salt': salt,
            'sign': sign
        }

        # 发送POST请求并解析响应结果
        try:
            response = requests.post(url, data=params)
            result = response.json()

            # 检查翻译结果是否存在
            translated_text = ''
            if 'trans_result' in result:
                for i in range(len(result['trans_result'])):
                    translated_text += result['trans_result'][i]['dst'] + '\n'
                return translated_text
            else:
                print(f"翻译失败，错误码：{result.get('error_code', '未知')}")
                return None
        except Exception as e:
            print(f"请求异常：{str(e)}")
            return None

    def logic(self):
        appid, secret_key = global_config.get("apikey", "baidu_translate").split("-")
        query = self.get_input_val("string")
        language = self.conbo_language.value()
        language_code = self.languages[language]
        translated_result = self.run_async_task(self.baidu_translate, appid, secret_key, query,  "auto", language_code)

        self.set_output_val("string", translated_result)

    def get_widget_input(self):
        language = self.conbo_language.value()

        return {"language": language}

    def set_widget_input(self, inputs):
        self.conbo_language.setCurrentText(inputs.get("language", "英语"))
