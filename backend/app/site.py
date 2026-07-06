"""Site configuration: content/site.yml holds all editable site settings
(title, footer, ICP/police beian toggles, Twikoo, agreement, nav, etc.)."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from .config import settings


DEFAULT_SITE_CONFIG: dict[str, Any] = {
    "title": "班级纪念站",
    "subtitle": "2026届4班纪念站",
    "author": "2026届4班",
    "description": "记录班级回忆的纪念站",
    "license": "CC BY-NC-SA 4.0",
    "license_url": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
    "email": "474985908@qq.com",
    "start_year": 2025,
    "nav": [
        {"name": "首页", "link": "/"},
        {"name": "归档", "link": "/archives/"},
        {"name": "图库", "link": "/gallery/"},
        {"name": "关于", "link": "/about/"},
    ],
    "hero": {
        "enable": True,
        "image": "",
        "title": "",
        "subtitle": "",
        "mask_alpha": 0.35,
        "height": 70,
    },
    "footer_html": "",  # extra custom HTML before the beian line
    "beian": {
        "icp": {"enable": True, "text": "鄂ICP备2026016149号-1",
                "url": "https://beian.miit.gov.cn/"},
        "police": {"enable": True, "text": "鄂公安网备42030402000182号",
                   "code": "42030402000182",
                   "url": "http://www.beian.gov.cn/portal/registerSystemInfo?recordcode=42030402000182"},
    },
    "twikoo": {
        "enable": True,
        "env_id": "https://twikoo.zichenccc.cn/.netlify/functions/twikoo",
        "cdn": "https://lib.baomitu.com/twikoo/1.6.8/twikoo.all.min.js",
    },
    "agreement": {
        "enable": True,
        "storage_key": "site_agreement_v1",
        "countdown_seconds": 7,
        "pages": ["用户协议", "免责声明"],
    },
    "gallery": {"enable": True, "title": "班级图库"},
    "analytics": {"baidu_id": ""},
}


def load_site_config() -> dict[str, Any]:
    p: Path = settings.site_yml_path
    if not p.exists():
        return deepcopy(DEFAULT_SITE_CONFIG)
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception:
        return deepcopy(DEFAULT_SITE_CONFIG)
    # Deep-merge over defaults so missing keys fall back
    return _merge(deepcopy(DEFAULT_SITE_CONFIG), data)


def save_site_config(cfg: dict[str, Any]) -> dict[str, Any]:
    p = settings.site_yml_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return cfg


def _merge(base: dict, override: dict) -> dict:
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _merge(base[k], v)
        else:
            base[k] = v
    return base
