from aqt import mw
from aqt.qt import QAction
from aqt.utils import showInfo, qconnect
from anki.utils import strip_html

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

JA_NLP_MODEL = "ja_core_news_sm"
if not spacy.util.is_package(JA_NLP_MODEL):
    spacy.cli.download(JA_NLP_MODEL)

def count_cards() -> None:

    all_card_ids = mw.col.find_cards("")

    nlp = spacy.load(JA_NLP_MODEL)

    word_retrievabilities = {}
    for card_id in all_card_ids:

        card_retrievability = mw.col.card_stats_data(card_id).fsrs_retrievability

        card_text = strip_html(mw.col.get_card(card_id).question())
        doc = nlp(card_text)

        for token in doc:

            lemma = str(token.lemma_)

            if lemma not in word_retrievabilities or word_retrievabilities[lemma] < card_retrievability:
                word_retrievabilities[lemma] = card_retrievability

    num_lemmas = int(sum(word_retrievabilities.values()))

    print(word_retrievabilities)

    showInfo(f"You know {num_lemmas} lemmas")

action = QAction("Anki Vocabulary Calculator")
qconnect(action.triggered, count_cards)
mw.form.menuTools.addAction(action)