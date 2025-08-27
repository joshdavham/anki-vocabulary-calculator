from aqt import mw, gui_hooks
from aqt.qt import QAction, QMessageBox
from aqt.utils import showInfo, qconnect
from anki.utils import strip_html
from importlib.resources import files
import importlib.util

import sys, subprocess
from pathlib import Path

VENDOR = Path(__file__).parent / "vendor"
VENDOR.mkdir(exist_ok=True)
if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

def maybe_prompt_install() -> None:

    if not importlib.util.find_spec("spacy"):

        msg = QMessageBox(mw)
        msg.setText("Anki Vocabulary Calculator needs to install some additional libraries.\n"
                    "Would you like to complete the installation now?")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)
        result = msg.exec()

        if result == QMessageBox.StandardButton.Yes:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "spacy", "--only-binary=:all:", "--target", str(VENDOR)])

def count_cards() -> None:

    import spacy

    ja_words_txt_path = files(__package__) / "ja_words.txt"
    with open(ja_words_txt_path, "r", encoding="utf-8") as file:
        JA_WORD_LIST = file.read().splitlines()

    JA_NLP_MODEL = "ja_core_news_sm"
    if not spacy.util.is_package(JA_NLP_MODEL):
        spacy.cli.download(JA_NLP_MODEL)
    nlp = spacy.load(JA_NLP_MODEL)

    all_card_ids = mw.col.find_cards("")

    lemma_retrievabilities = {}
    for card_id in all_card_ids:

        card_retrievability = mw.col.card_stats_data(card_id).fsrs_retrievability

        card_text = strip_html(mw.col.get_card(card_id).question())
        doc = nlp(card_text)

        for token in doc:

            lemma = str(token.lemma_)

            if lemma in JA_WORD_LIST:

                if lemma not in lemma_retrievabilities or lemma_retrievabilities[lemma] < card_retrievability:
                    lemma_retrievabilities[lemma] = card_retrievability

    num_lemmas = int(sum(lemma_retrievabilities.values()))

    showInfo(f"You currently know at least {num_lemmas} Japanese base words.")

action = QAction("Anki Vocabulary Calculator")
qconnect(action.triggered, count_cards)
mw.form.menuTools.addAction(action)

gui_hooks.profile_did_open.append(maybe_prompt_install)