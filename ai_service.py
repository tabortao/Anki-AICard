import json
import urllib.request
import urllib.error
from typing import List, Dict, Tuple

class AIService:
    @staticmethod
    def _make_request(api_base: str, api_key: str, payload: dict, timeout: int) -> dict:
        url = api_base.rstrip("/") + "/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    @classmethod
    def test_connection(cls, api_base: str, api_key: str, model: str, timeout: int = 10) -> Tuple[bool, str]:
        """连通性测试"""
        if not api_key.strip():
            return False, "API Key 不能为空"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 5
        }
        try:
            cls._make_request(api_base, api_key, payload, timeout)
            return True, "连接成功！接口与模型可用。"
        except urllib.error.HTTPError as e:
            return False, f"HTTP 错误 ({e.code}): {e.read().decode('utf-8', errors='ignore')}"
        except Exception as e:
            return False, f"网络请求异常: {str(e)}"

    @classmethod
    def generate_cards(cls, material: str, fields: List[str], api_base: str, api_key: str, model: str, timeout: int = 60) -> List[Dict[str, str]]:
        """根据材料和模板字段批量生成卡片"""
        system_prompt = (
            "你是一个专业的 Anki 卡片制作专家。请根据用户提供的材料，提炼关键知识点并生成卡片。\n"
            f"目标模板包含以下字段：{json.dumps(fields, ensure_ascii=False)}。\n"
            "输出必须是严格的 JSON 数组格式，不要包含任何 markdown 代码块标识（如 ```json），每个对象必须且仅包含上述字段名称作为键。\n"
            "如果内容不足以填满某些字段，可设为空字符串，但核心问答字段不可为空。"
        )
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": material}
            ],
            "temperature": 0.3
        }

        resp = cls._make_request(api_base, api_key, payload, timeout)
        content = resp["choices"][0]["message"]["content"].strip()
        
        # 兼容处理带 markdown 代码块包裹的情况
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).strip()

        cards_data = json.loads(content)
        if not isinstance(cards_data, list):
            raise ValueError("AI 返回的数据不是有效的卡片列表结构")

        # 过滤全空卡片
        valid_cards = []
        for item in cards_data:
            if isinstance(item, dict) and any(str(item.get(f, "")).strip() for f in fields):
                valid_cards.append({f: str(item.get(f, "")).strip() for f in fields})
        return valid_cards