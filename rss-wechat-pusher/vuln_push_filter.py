"""
漏洞信息推送收紧：仍分类/入库，企微推送前再过滤。

放行条件（满足其一即可）：
  A. 命中金融信息系统常用组件/软件白名单（如 PHP、Spring、Nginx…）
  B. 命中大规模 / 高危利用信号（CVSS 高危、RCE、在野利用等）

可用环境变量覆盖：
  VULN_PUSH_FILTER=0          — 关闭过滤（全部漏洞照推）
  VULN_COMPONENT_WHITELIST    — 逗号分隔，追加到默认组件词
  VULN_SEVERITY_EXTRA         — 逗号分隔，追加到默认高危词
"""
from __future__ import annotations

import os
import re
from typing import List, Optional, Sequence, Tuple

# 金融/核心业务常见技术栈与基础设施（可配置追加）
_DEFAULT_COMPONENTS: Tuple[str, ...] = (
    # 语言与运行时
    "php",
    "java",
    "jdk",
    "jre",
    "python",
    "nodejs",
    "node.js",
    ".net",
    "dotnet",
    "golang",
    "go语言",
    # Web / 中间件
    "spring",
    "spring boot",
    "springboot",
    "struts",
    "tomcat",
    "jetty",
    "weblogic",
    "websphere",
    "jboss",
    "wildfly",
    "nginx",
    "apache http",
    "apache httpd",
    "httpd",
    "iis",
    "openresty",
    # 数据与缓存
    "mysql",
    "mariadb",
    "postgresql",
    "postgres",
    "oracle database",
    "sql server",
    "mssql",
    "redis",
    "mongodb",
    "elasticsearch",
    "kafka",
    "rabbitmq",
    "activemq",
    # OS / 基础
    "linux",
    "ubuntu",
    "centos",
    "rhel",
    "redhat",
    "windows server",
    "windows",
    "openssl",
    "openssh",
    "ssh",
    # 容器与常见运维
    "docker",
    "kubernetes",
    "k8s",
    "containerd",
    # 身份 / 网关 / 常见企业组件
    "oauth",
    "keycloak",
    "ldap",
    "active directory",
    "vpn",
    "fortinet",
    "citrix",
    "vmware",
    "vcenter",
    "esxi",
    # 国产 / 常见业务相关（可再配）
    "达梦",
    "人大金仓",
    "kingbase",
    "tongweb",
    "东方通",
    "宝兰德",
)

# 大规模 / 高危信号
_DEFAULT_SEVERITY: Tuple[str, ...] = (
    r"\bcvss\s*[:=]?\s*(9(\.\d)?|10(\.0)?)\b",
    r"\bcvss\s*[:=]?\s*([789](\.\d)?)\b",
    r"\bcritical\b",
    r"\bsevere\b",
    r"严重",
    r"高危",
    r"超危",
    r"\brce\b",
    r"remote\s+code\s+execution",
    r"远程代码执行",
    r"远程命令执行",
    r"未授权",
    r"unauthorized",
    r"authentication\s+bypass",
    r"权限绕过",
    r"认证绕过",
    r"in[\s-]?the[\s-]?wild",
    r"actively\s+exploited",
    r"已知利用",
    r"在野利用",
    r"大规模",
    r"大范围",
    r"worm",
    r"蠕虫",
    r"0[\s-]?day",
    r"零日",
    r"n[\s-]?day",
    r"供应链",
    r"supply[\s-]?chain",
)


def _env_flag_off(name: str) -> bool:
    return (os.getenv(name) or "1").strip().lower() in ("0", "false", "no", "off")


def _split_extra(name: str) -> List[str]:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def _cfg_list(name: str, default: Sequence[str]) -> List[str]:
    try:
        import config as cfg

        val = getattr(cfg, name, None)
        if isinstance(val, (list, tuple)) and val:
            return [str(x).strip() for x in val if str(x).strip()]
    except ImportError:
        pass
    return list(default)


def component_patterns() -> List[re.Pattern]:
    words = _cfg_list("VULN_COMPONENT_WHITELIST", _DEFAULT_COMPONENTS)
    words = list(dict.fromkeys(words + _split_extra("VULN_COMPONENT_WHITELIST")))
    out = []
    for w in words:
        w = w.strip()
        if not w:
            continue
        # 短词加边界，中文/带点词用普通包含
        if re.fullmatch(r"[A-Za-z0-9_.+-]+", w) and len(w) <= 4:
            out.append(re.compile(rf"(?i)(?<![A-Za-z0-9]){re.escape(w)}(?![A-Za-z0-9])"))
        else:
            out.append(re.compile(re.escape(w), re.I))
    return out


def severity_patterns() -> List[re.Pattern]:
    raw: List[str] = list(_DEFAULT_SEVERITY)
    raw.extend(_split_extra("VULN_SEVERITY_EXTRA"))
    try:
        import config as cfg

        cfg_extra = getattr(cfg, "VULN_SEVERITY_EXTRA", None)
        if isinstance(cfg_extra, (list, tuple)):
            raw.extend(str(x) for x in cfg_extra if str(x).strip())
    except ImportError:
        pass
    out = []
    for p in raw:
        try:
            out.append(re.compile(p, re.I))
        except re.error:
            out.append(re.compile(re.escape(p), re.I))
    return out


def vuln_push_filter_enabled() -> bool:
    return not _env_flag_off("VULN_PUSH_FILTER")


def should_push_vulnerability(title: str, summary: str = "") -> Tuple[bool, str]:
    """
    返回 (是否推送, 原因说明)。
    非漏洞条目请勿调用。
    """
    if not vuln_push_filter_enabled():
        return True, "过滤关闭"
    blob = f"{title or ''}\n{summary or ''}"
    for pat in component_patterns():
        if pat.search(blob):
            return True, f"命中常用组件: {pat.pattern}"
    for pat in severity_patterns():
        if pat.search(blob):
            return True, f"命中高危/大规模信号: {pat.pattern}"
    return False, "未命中金融常用组件且无大规模/高危信号"


def filter_timed_items_for_vuln_push(
    items: Sequence[dict],
) -> Tuple[List[dict], List[dict]]:
    """
    对定时档条目分流：keep 推送；skip 为漏洞但不值得推。
    非「漏洞信息」一律 keep。
    """
    keep: List[dict] = []
    skip: List[dict] = []
    for it in items:
        if (it.get("category") or "") != "漏洞信息":
            keep.append(it)
            continue
        ok, reason = should_push_vulnerability(it.get("title") or "", it.get("summary") or "")
        if ok:
            keep.append(it)
        else:
            skip.append({**it, "_vuln_skip_reason": reason})
    return keep, skip
