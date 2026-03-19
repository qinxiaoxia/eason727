"""
LLM 调用工具：支持多模型自动切换
当某个 API 额度用尽或失败时，自动尝试下一个
"""
import json
import os
from typing import List, Optional, Tuple

import requests


def get_llm_providers() -> List[Tuple[str, str, str]]:
    """
    获取要尝试的 LLM 提供商列表，按顺序尝试。
    优先使用 LLM_PROVIDERS_JSON（多模型），否则用单个 LLM_API_KEY/BASE_URL/MODEL
    """
    providers_json = os.getenv("LLM_PROVIDERS_JSON")
    arr = None
    if providers_json:
        try:
            arr = json.loads(providers_json)
        except json.JSONDecodeError:
            arr = None
    if not arr:
        try:
            from config import LLM_PROVIDERS
            if LLM_PROVIDERS:
                arr = LLM_PROVIDERS
        except ImportError:
            pass
    if arr:
        out = []
        for p in arr:
            if isinstance(p, dict):
                key = p.get("api_key") or p.get("apiKey", "")
                url = p.get("base_url") or p.get("baseUrl", "")
                model = p.get("model", "")
            elif isinstance(p, (list, tuple)) and len(p) >= 3:
                key, url, model = p[0], p[1], p[2]
            else:
                continue
            if key and url and model:
                out.append((key, url, model))
        if out:
            return out

    # 同一 API 下多模型：LLM_MODELS_JSON = ["qwen-turbo","qwen-math-turbo",...]，额度用尽自动换下一个
    models_json = os.getenv("LLM_MODELS_JSON")
    models_list = None
    if models_json:
        try:
            models_list = json.loads(models_json)
        except json.JSONDecodeError:
            models_list = None
    if not models_list:
        try:
            from config import LLM_MODELS
            if LLM_MODELS:
                models_list = LLM_MODELS
        except ImportError:
            pass
    if models_list and isinstance(models_list, list):
        key = os.getenv("LLM_API_KEY")
        url = os.getenv("LLM_BASE_URL")
        if not (key and url):
            try:
                from config import LLM_API_KEY as ck, LLM_BASE_URL as cu
                key, url = ck or "", cu or ""
            except ImportError:
                pass
        if key and url:
            return [(key, url, m) for m in models_list if isinstance(m, str) and m.strip()]

    # 单模型配置（env 或 config）
    key = os.getenv("LLM_API_KEY")
    url = os.getenv("LLM_BASE_URL")
    model = os.getenv("LLM_MODEL")
    if not (key and url and model):
        try:
            from config import LLM_API_KEY as ck, LLM_BASE_URL as cu, LLM_MODEL as cm
            key, url, model = ck or "", cu or "", cm or ""
        except ImportError:
            pass
    if key and url and model:
        return [(key, url, model)]
    return []


def call_llm_with_fallback(messages: list, max_tokens: int = 20) -> Optional[str]:
    """
    按顺序尝试各模型，直到有一个成功。失败（额度用尽、超时等）则换下一个。
    """
    providers = get_llm_providers()
    for api_key, base_url, model in providers:
        try:
            url = base_url.rstrip("/") + "/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0,
            }
            r = requests.post(url, json=payload, headers=headers, timeout=15)
            r.raise_for_status()
            data = r.json()
            content = (data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
            if content:
                # 打印当前使用的模型（可在 Actions 日志中查看）
                print(f"[LLM] 使用模型: {model}", flush=True)
                return content
        except Exception:
            continue
    return None
