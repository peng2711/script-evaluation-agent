import os
import json
import httpx
from .base import LLMClient
from .errors import LLMAPIError, LLMValidationError

class GeminiLLMClient(LLMClient):
    """
    GeminiLLMClient：使用 httpx 直接进行 Google Gemini Developer REST API 请求。
    """
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.model = os.getenv("GEMINI_MODEL", "gemini-1.5-pro").strip()

    def generate_text(self, prompt: str, **kwargs) -> str:
        if not self.api_key:
            raise LLMAPIError("GEMINI_API_KEY 未配置，无法调用 Gemini API。")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {
            "Content-Type": "application/json"
        }
        
        system_prompt = kwargs.get("system_prompt")
        full_text = (f"{system_prompt}\n\n" if system_prompt else "") + prompt
        
        payload = {
            "contents": [
                {
                    "parts": [{"text": full_text}]
                }
            ],
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.1)
            }
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                res_data = response.json()
                return res_data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            raise LLMAPIError(f"Gemini API 调用失败: {str(e)}") from e

    def generate_json(self, prompt: str, schema: dict, **kwargs) -> dict:
        schema_instruction = f"\n请输出符合以下 JSON Schema 的 JSON 字符串：\n{json.dumps(schema, ensure_ascii=False)}"
        full_prompt = prompt + schema_instruction

        if not self.api_key:
            raise LLMAPIError("GEMINI_API_KEY 未配置，无法调用 Gemini API。")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {
            "Content-Type": "application/json"
        }
        
        system_prompt = kwargs.get("system_prompt")
        full_text = (f"{system_prompt}\n\n" if system_prompt else "") + full_prompt

        payload = {
            "contents": [
                {
                    "parts": [{"text": full_text}]
                }
            ],
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.1),
                "responseMimeType": "application/json"
            }
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                res_data = response.json()
                content = res_data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            raise LLMAPIError(f"Gemini API 结构化调用失败: {str(e)}") from e

        # 清洗并解析 JSON 结果
        try:
            cleaned = self._clean_json_string(content)
            result = json.loads(cleaned)
        except Exception as json_err:
            raise LLMValidationError(f"Gemini 返回内容无法解析为 JSON: {content}。错误: {str(json_err)}") from json_err

        # 进行基础的 schema 校验
        self._validate_schema(result, schema)
        return result

    def _clean_json_string(self, content: str) -> str:
        content = content.strip()
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        return content

    def _validate_schema(self, data: dict, schema: dict):
        """
        轻量级的 schema 键值存在性与类型核验。
        """
        if not isinstance(data, dict):
            raise LLMValidationError(f"期望 JSON 对象，但得到: {type(data).__name__}")

        properties = schema.get("properties", {})
        required = schema.get("required", [])

        # 校验必填字段
        for req_field in required:
            if req_field not in data:
                raise LLMValidationError(f"缺失必选字段: '{req_field}'")

        # 校验字段类型
        for key, value in data.items():
            if key in properties:
                expected_type = properties[key].get("type")
                if expected_type == "array" and not isinstance(value, list):
                    raise LLMValidationError(f"字段 '{key}' 期望为 array，但实际类型为: {type(value).__name__}")
                elif expected_type == "integer":
                    if isinstance(value, bool) or not isinstance(value, int):
                        raise LLMValidationError(f"字段 '{key}' 期望为 integer，但实际类型为: {type(value).__name__}")
                elif expected_type == "number":
                    if isinstance(value, bool) or not isinstance(value, (int, float)):
                        raise LLMValidationError(f"字段 '{key}' 期望为 number，但实际类型为: {type(value).__name__}")
                elif expected_type == "boolean" and not isinstance(value, bool):
                    raise LLMValidationError(f"字段 '{key}' 期望为 boolean，但实际类型为: {type(value).__name__}")
                elif expected_type == "string" and not isinstance(value, str):
                    raise LLMValidationError(f"字段 '{key}' 期望为 string，但实际类型为: {type(value).__name__}")
