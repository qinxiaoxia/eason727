"""
LLM 调用工具：支持多模型自动切换
当某个 API 额度用尽或失败时，自动尝试下一个

purpose:
  - default：分类、摘要等（LLM_MODELS_JSON / LLM_MODELS）
  - translate：标题/短句翻译（LLM_TRANSLATE_MODELS_JSON；支持 qwen-mt-*）
  - ioc：监管机构 IOC 提取（LLM_IOC_MODELS_JSON / LLM_IOC_MODELS，未配则回退 default）
"""
import json
import os
from typing import Any, Dict, List, Optional, Tuple

import requests

# 网安标题翻译领域提示（Qwen-MT domains 仅支持英文）
_MT_SECURITY_DOMAINS = (
    "Cybersecurity news headlines and vulnerability advisories. "
    "Keep CVE IDs, product names, vendor names, and malware family names in original form when appropriate. "
    "Prefer concise Simplified Chinese news-headline style."
)


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


def is_mt_model(model: str) -> bool:
    return (model or "").strip().lower().startswith("qwen-mt-")


def _is_mt_model(model: str) -> bool:
    return is_mt_model(model)


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

    if purpose == "translate":
        models = _parse_models_json(os.getenv("LLM_TRANSLATE_MODELS_JSON"))
        if models:
            return models
        try:
            from config import LLM_TRANSLATE_MODELS
            if LLM_TRANSLATE_MODELS:
                return [m for m in LLM_TRANSLATE_MODELS if isinstance(m, str) and m.strip()]
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
    # 翻译 / IOC 用专用模型列表，不吃通用 PROVIDERS
    if providers_json and purpose not in ("ioc", "translate"):
        try:
            arr = json.loads(providers_json)
        except json.JSONDecodeError:
            arr = None
    if not arr and purpose not in ("ioc", "translate"):
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
    if purpose in ("ioc", "translate") and not models_list:
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

    if purpose in ("ioc", "translate"):
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


def _last_user_text(messages: list) -> str:
    for m in reversed(messages or []):
        if isinstance(m, dict) and m.get("role") == "user":
            return (m.get("content") or "").strip()
    if messages and isinstance(messages[0], dict):
        return (messages[0].get("content") or "").strip()
    return ""


def _mt_payload_messages(text: str) -> List[dict]:
    # Qwen-MT：仅支持单条 user message，内容为待译原文
    return [{"role": "user", "content": text}]


def call_llm_with_fallback(
    messages: list,
    max_tokens: int = 20,
    system: Optional[str] = None,
    purpose: str = "default",
    translation_options: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    按顺序尝试各模型，直到有一个成功。失败（额度用尽、超时等）则换下一个。
    system：可选系统提示（qwen-mt-* 会忽略，改走 translation_options）。
    purpose：default=分类/摘要；translate=翻译；ioc=监管机构 IOC 提取。
    """
    purpose = (purpose or "default").strip().lower()
    base_msgs: List[dict] = list(messages or [])
    providers = get_llm_providers(purpose)
    for api_key, base_url, model in providers:
        try:
            url = base_url.rstrip("/") + "/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            use_mt = _is_mt_model(model)
            if use_mt:
                text = _last_user_text(base_msgs)
                if not text:
                    continue
                opts = dict(translation_options or {})
                opts.setdefault("source_lang", "auto")
                opts.setdefault("target_lang", "Chinese")
                opts.setdefault("domains", _MT_SECURITY_DOMAINS)
                payload = {
                    "model": model,
                    "messages": _mt_payload_messages(text),
                    "translation_options": opts,
                }
            else:
                msgs = list(base_msgs)
                if system:
                    msgs = [{"role": "system", "content": system}] + msgs
                payload = {
                    "model": model,
                    "messages": msgs,
                    "max_tokens": max_tokens,
                    "temperature": 0,
                }
            timeout = 45 if purpose == "ioc" else (60 if max_tokens and max_tokens >= 800 else 25)
            r = requests.post(url, json=payload, headers=headers, timeout=timeout)
            if r.status_code >= 400:
                err = (r.text or "")[:180].replace("\n", " ")
                print(f"[LLM] {model} HTTP {r.status_code}: {err}", flush=True)
                continue
            data = r.json()
            content = (data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
            if content:
                tag = "IOC" if purpose == "ioc" else ("译" if purpose == "translate" or use_mt else "LLM")
                print(f"[{tag}] 使用模型: {model}", flush=True)
                return content
        except Exception as e:
            print(f"[LLM] {model} 调用异常: {e}", flush=True)
            continue
    return None
