#!/usr/bin/env python3
"""fix6_gui.py - Interface graphique FIX-6"""

import sys
import os
import shutil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout,
    QHBoxLayout, QWidget, QLabel, QComboBox,
    QSizePolicy, QFileDialog, QMessageBox,
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt

from fix6_model import generate_puzzle_at_level, verify_puzzle, DIFFICULTY_HINTS
from fix6_visualization import draw_fix6


class Fix6App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FIX-6 Generator")
        self.setMinimumSize(600, 700)
        self.resize(800, 900)
        self.puzzle = None
        self.image_paths = []
        self.save_counter = 1
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        title = QLabel("Générateur FIX-6")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Niveau de difficulté
        diff_layout = QHBoxLayout()
        diff_layout.addWidget(QLabel("Niveau :"))
        self.difficulty_combo = QComboBox()
        # (label affiché, clé interne)
        self._difficulty_options = [
            ("Très facile (15 indices)", "tres_facile"),
            ("Facile (8-10 indices)",    "facile"),
            ("Moyen (5-8 indices)",      "moyen"),
            ("Difficile (1-3 indices)",  "difficile"),
            ("Sans indices",             "sans_indices"),
        ]
        for label_text, key in self._difficulty_options:
            self.difficulty_combo.addItem(label_text, key)
        self.difficulty_combo.setCurrentIndex(2)  # défaut: Moyen
        diff_layout.addWidget(self.difficulty_combo)
        diff_layout.addStretch()
        layout.addLayout(diff_layout)

        gen_btn = QPushButton("Générer un puzzle")
        gen_btn.clicked.connect(self.generate)
        layout.addWidget(gen_btn)

        save_layout = QHBoxLayout()
        save_png = QPushButton("Enregistrer (PNG)")
        save_png.clicked.connect(self.save_png)
        save_layout.addWidget(save_png)
        layout.addLayout(save_layout)

        images_layout = QHBoxLayout()
        self.puzzle_label = QLabel("Générez un puzzle")
        self.solution_label = QLabel("")
        for lbl in (self.puzzle_label, self.solution_label):
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setMinimumSize(100, 100)
            lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            lbl.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
            images_layout.addWidget(lbl, 1)
        layout.addLayout(images_layout)

    def _selected_difficulty(self) -> str:
        return self.difficulty_combo.itemData(self.difficulty_combo.currentIndex()) or "moyen"

    def generate(self):
        self.solution_label.setText("Génération...")
        self.puzzle_label.setText("")
        QApplication.processEvents()

        difficulty = self._selected_difficulty()
        puzzle = generate_puzzle_at_level(difficulty=difficulty)
        if not puzzle:
            QMessageBox.critical(self, "Échec",
                                 f"Impossible de générer un puzzle '{difficulty}'.")
            self.solution_label.setText("Échec")
            return

        self.puzzle = puzzle
        verify_puzzle(puzzle)

        temp = "temp_fix6"
        os.makedirs(temp, exist_ok=True)
        self.image_paths = draw_fix6(puzzle, os.path.join(temp, "fix6"))
        self._update_display()

    def _update_display(self):
        if not self.image_paths:
            return
        # image_paths[0]=solution, [1]=puzzle
        for path, label in zip(self.image_paths, [self.solution_label, self.puzzle_label]):
            pix = QPixmap(path)
            side = min(max(50, label.width() - 20), max(50, label.height() - 20))
            label.setPixmap(pix.scaled(side, side, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def save_png(self):
        if not self.image_paths:
            QMessageBox.warning(self, "Attention", "Aucun puzzle généré.")
            return
        save_dir = QFileDialog.getExistingDirectory(self, "Dossier", os.path.expanduser("~"))
        if not save_dir:
            return
        n = self.save_counter
        for img in self.image_paths:
            suffix = "_solution" if "solution" in img else ""
            shutil.copy2(img, os.path.join(save_dir, f"FIX6_{n}{suffix}.png"))
        self.save_counter += 1
        QMessageBox.information(self, "OK", f"Sauvegardé dans {save_dir}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.image_paths:
            self._update_display()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Fix6App()
    window.show()
    sys.exit(app.exec_())
