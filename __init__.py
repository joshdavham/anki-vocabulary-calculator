from aqt import mw, gui_hooks
from aqt.qt import QAction, QMessageBox, QPixmap
from aqt.utils import qconnect, tooltip
from anki.utils import strip_html
from importlib.resources import files
import importlib.util
from typing import Tuple
from concurrent.futures import Future

import sys
import subprocess
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
                sys.executable,
                "-m",
                "pip",
                "install",
                "spacy",
                "--only-binary=:all:",
                "--target",
                str(VENDOR),
            ]

            process = subprocess.run(cmd, capture_output=True, text=True)
            return process.returncode, process.stdout, process.stderr

        def on_done(future: Future[int, str, str]) -> None:
            returncode, stdout, stderr = future.result()
            if returncode == 0:

                action = QAction("Anki Vocabulary Calculator", mw)
                qconnect(action.triggered, count_cards)
                mw.form.menuTools.addAction(action)

                box = QMessageBox(mw)
                box.setIconPixmap(QPixmap(str(Path(__file__).parent / "anki_vocabulary_calculator_icon.png")))
                box.setWindowTitle("Anki Vocabulary Calculator")
                box.setText("Anki Vocabulary Calculator successfully installed!\n\nTools > Anki Vocabulary Calculator")
                confirm_button = box.addButton("Okay", QMessageBox.ButtonRole.AcceptRole)
                box.setDefaultButton(confirm_button)
                box.exec()

            else:

                box = QMessageBox(mw)
                box.setIconPixmap(QPixmap(str(Path(__file__).parent / "anki_vocabulary_calculator_icon.png")))
                box.setWindowTitle("Anki Vocabulary Calculator")
                box.setText("Anki Vocabulary Calculator installation failed.\n\nPlease make sure you're connected to the internet for installation.")
                confirm_button = box.addButton("Okay", QMessageBox.ButtonRole.AcceptRole)
                box.setDefaultButton(confirm_button)
                box.exec()

        mw.taskman.run_in_background(task=task, on_done=on_done)

    else:

        action = QAction("Anki Vocabulary Calculator", mw)
        qconnect(action.triggered, count_cards)
        mw.form.menuTools.addAction(action)


def count_cards() -> None:
    box = QMessageBox(mw)
    box.setIconPixmap(QPixmap(str(Path(__file__).parent / "anki_vocabulary_calculator_icon.png")))
    box.setWindowTitle("Anki Vocabulary Calculator")
    box.setText("Calculate Japanese vocabulary size?")
    calculate_button = box.addButton("Calculate!", QMessageBox.ButtonRole.AcceptRole)
    _ = box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
    box.setDefaultButton(calculate_button)
    box.exec()

    if box.clickedButton() == calculate_button:
        tooltip("Calculating vocabulary... Result will display when done.", period=5000)

        import spacy

        def task() -> int:
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
                card_retrievability = mw.col.card_stats_data(
                    card_id
                ).fsrs_retrievability

                card_text = strip_html(mw.col.get_card(card_id).question())
                doc = nlp(card_text)

                for token in doc:
                    lemma = str(token.lemma_)

                    if lemma in JA_WORD_LIST:
                        if (
                            lemma not in lemma_retrievabilities
                            or lemma_retrievabilities[lemma] < card_retrievability
                        ):
                            lemma_retrievabilities[lemma] = card_retrievability

            num_lemmas = int(sum(lemma_retrievabilities.values()))

            return num_lemmas

        def on_done(future: Future[int]):
            num_lemmas = future.result()

            box = QMessageBox(mw)
            box.setIconPixmap(QPixmap(str(Path(__file__).parent / "anki_vocabulary_calculator_icon.png")))
            box.setWindowTitle("Anki Vocabulary Calculator")
            box.setText(f"You currently know at least\n\n{num_lemmas}\n\nJapanese base words")
            confirm_button = box.addButton("Okay", QMessageBox.ButtonRole.AcceptRole)
            box.setDefaultButton(confirm_button)
            box.exec()

        mw.taskman.run_in_background(task=task, on_done=on_done)


gui_hooks.profile_did_open.append(maybe_prompt_install)
