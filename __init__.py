from aqt.utils import showInfo

import sys, subprocess
from pathlib import Path

VENDOR = Path(__file__).parent / "vendor"
VENDOR.mkdir(exist_ok=True)
if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

try:
    import spacy
except Exception:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "spacy", "--only-binary=:all:", "--target", str(VENDOR)])
    import spacy

try:
    nlp = spacy.load("ja_core_news_sm")
except Exception:
    from spacy.cli import download
    download("ja_core_news_sm")
    nlp = spacy.load("ja_core_news_sm")


