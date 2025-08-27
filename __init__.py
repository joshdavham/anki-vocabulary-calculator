from aqt import mw, gui_hooks
from aqt.qt import QAction, QMessageBox
from aqt.utils import showInfo, qconnect, tooltip
from anki.utils import strip_html
from importlib.resources import files
import importlib.util
import os
from typing import Tuple
from concurrent.futures import Future

import sys, subprocess
from pathlib import Path

VENDOR = Path(__file__).parent / "vendor"
VENDOR.mkdir(exist_ok=True)
if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

def maybe_prompt_install() -> None:

    if not importlib.util.find_spec("spacy"):

        tooltip("Installing Anki Vocaulary Calculator... This may take a minute.")

        def task() -> Tuple[int, str, str]:
            cmd = [
                sys.executable, "-m", "pip", "install", "spacy",
                "--only-binary=:all:", "--target", str(VENDOR),
            ]

            process = subprocess.run(cmd, capture_output=True, text=True)
            return process.returncode, process.stdout, process.stderr

        def on_done(future: Future[int, str, str]) -> None:
            returncode, stdout, stderr = future.result()
            if returncode == 0:
                showInfo(f"Anki Vocabulary Calculator has been successfully installed!\n\n"
                         f"Go to Tools > Anki Vocabulary Calculator to use it.")
            else:
                showInfo(
                    f"Anki Vocabulary Calculator installation failed.\n\n"
                    f"Please make sure you're connected to the internet for installation."
                )

        mw.taskman.run_in_background(task=task, on_done=on_done)

def count_cards() -> None:

    box = QMessageBox(mw)
    box.setIcon(QMessageBox.Icon.Information)
    box.setWindowTitle("Anki Vocabulary Calculator")
    box.setText("Which language would you like to calculate?")
    # box.setDetailedText("Some detailed text")
    japanese_button = box.addButton("Japanese 🇯🇵", QMessageBox.ButtonRole.AcceptRole)
    cancel_button = box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
    box.setDefaultButton(japanese_button)
    box.exec()

    if box.clickedButton() == japanese_button:

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