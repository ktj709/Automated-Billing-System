import json
from pathlib import Path

FLAGS_FILE = Path(__file__).resolve().parent.parent / "feature_flags.json"

DEFAULT_FLAGS = {
    "enable_gemini_3_pro": False
}


def _ensure_file():
    if not FLAGS_FILE.exists():
        FLAGS_FILE.write_text(json.dumps(DEFAULT_FLAGS, indent=2))


def get_flags():
    _ensure_file()
    try:
        return json.loads(FLAGS_FILE.read_text())
    except Exception:
        FLAGS_FILE.write_text(json.dumps(DEFAULT_FLAGS, indent=2))
        return DEFAULT_FLAGS.copy()


def get_flag(name: str):
    flags = get_flags()
    return flags.get(name, DEFAULT_FLAGS.get(name))


def set_flag(name: str, value):
    flags = get_flags()
    flags[name] = value
    FLAGS_FILE.write_text(json.dumps(flags, indent=2))
    return flags
