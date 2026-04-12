#!/usr/bin/env python3
"""fix6_gui.py - Interface graphique FIX-6"""

import sys
import os
import shutil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout,
    QHBoxLayout, QWidget, QLabel, QSizePolicy, QFileDialog, QMessageBox,
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt

from fix6_model import generate_puzzle, verify_puzzle
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

    def generate(self):
        self.solution_label.setText("Génération...")
        self.puzzle_label.setText("")
        QApplication.processEvents()

        puzzle = generate_puzzle()
        if not puzzle:
            QMessageBox.critical(self, "Échec", "Impossible de générer.")
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
