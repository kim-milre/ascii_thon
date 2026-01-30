# app/utils/audit.py
import os, json, uuid
from pathlib import Path
from datetime import datetime

AUDIT_DIR = Path(os.getenv("PIPE_AUDIT_DIR", "logs/pipeline"))
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

def _ts():
    return datetime.now().strftime("%Y%m%d-%H")

def dump_json(run_id: str, stage: str, name: str, obj):
    base = AUDIT_DIR / f"{_ts()}_{run_id}" / stage
    base.mkdir(parents=True, exist_ok=True)
    fp = base / f"{name}.json"
    fp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(fp)

def dump_text(run_id: str, stage: str, name: str, text: str):
    base = AUDIT_DIR / f"{_ts()}_{run_id}" / stage
    base.mkdir(parents=True, exist_ok=True)
    fp = base / f"{name}.txt"
    fp.write_text(text or "", encoding="utf-8")
    return str(fp)
