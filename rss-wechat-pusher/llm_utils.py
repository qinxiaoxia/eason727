"""
LLM 调用工具：支持多模型自动切换
当某个 API 额度用尽或失败时，自动尝试下一个

purpose:
  - default：分类、翻译等（LLM_MODELS_JSON / LLM_MODELS）
  - ioc：监管机构 IOC 提取（LLM_IOC_MODELS_JSON / LLM_IOC_MODELS，未配则回退 default）
"""
import json
import os
from typing import List, Optional, Tuple

import requests


def _parse_models_json(raw: Optional[str]) -> Optional[List[str]]:
    if not raw:
        return None
    try:
        arr = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(arr, list):
        return None
    out = [m.strip() for m in arr if isinstance(m, str) and m.strip()]
    return out or None


def _models_for_purpose(purpose: str) -> Optional[List[str]]:
    purpose = (purpose or "default").strip().lower()
    if purpose == "ioc":
        models = _parse_models_json(os.getenv("LLM_IOC_MODELS_JSON"))
        if models:
            return models
        try:
            from config import LLM_IOC_MODELS
            if LLM_IOC_MODELS:
                return [m for m in LLM_IOC_MODELS if isinstance(m, str) and m.strip()]
        except ImportError:
            pass
        return None

    models = _parse_models_json(os.getenv("LLM_MODELS_JSON"))
    if models:
        return models
    try:
        from config import LLM_MODELS
        if LLM_MODELS:
            return [m for m in LLM_MODELS if isinstance(m, str) and m.strip()]
    except ImportError:
        pass
    return None


def get_llm_providers(purpose: str = "default") -> List[Tuple[str, str, str]]:
    """
    获取要尝试的 LLM 提供商列表，按顺序尝试。
    优先使用 LLM_PROVIDERS_JSON（多模型），否则用单个 LLM_API_KEY/BASE_URL/MODEL
    """
    purpose = (purpose or "default").strip().lower()

    providers_json = os.getenv("LLM_PROVIDERS_JSON")
    arr = None
    if providers_json and purpose != "ioc":
        try:
            arr = json.loads(providers_json)
        except json.JSONDecodeError:
            arr = None
    if not arr and purpose != "ioc":
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

    models_list = _models_for_purpose(purpose)
    if purpose == "ioc" and not models_list:
        return get_llm_providers("default")

    if models_list:
        key = os.getenv("LLM_API_KEY")
        url = os.getenv("LLM_BASE_URL")
        if not (key and url):
            try:
                from config import LLM_API_KEY as ck, LLM_BASE_URL as cu
                key, url = ck or "", cu or ""
            except ImportError:
                pass
        if key and url:
            return [(key, url, m) for m in models_list]

    if purpose == "ioc":
        return get_llm_providers("default")

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


def call_llm_with_fallback(
    messages: list,
    max_tokens: int = 20,
    system: Optional[str] = None,
    purpose: str = "default",
) -> Optional[str]:
    """
    按顺序尝试各模型，直到有一个成功。失败（额度用尽、超时等）则换下一个。
    system：可选系统提示，会插入为第一条 message（适用于翻译等需统一约束的场景）。
    purpose：default=分类/翻译；ioc=监管机构 IOC 提取。
    """
    msgs: List[dict] = list(messages)
    if system:
        msgs = [{"role": "system", "content": system}] + msgs
    providers = get_llm_providers(purpose)
    for api_key, base_url, model in providers:
        try:
            url = base_url.rstrip("/") + "/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": model,
                "messages": msgs,
                "max_tokens": max_tokens,
                "temperature": 0,
            }
            timeout = 45 if purpose == "ioc" else 15
            r = requests.post(url, json=payload, headers=headers, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            content = (data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
            if content:
                tag = "IOC" if purpose == "ioc" else "LLM"
                print(f"[{tag}] 使用模型: {model}", flush=True)
                return content
        except Exception:
            continue
    return None
