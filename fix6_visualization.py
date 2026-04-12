#!/usr/bin/env python3
"""fix6_visualization.py - Rendu PNG des puzzles FIX-6."""

from PIL import Image, ImageDraw, ImageFont
import os

from fix6_model import GRID

TARGET_PX = 2000

BG_COLOR = "#D8D8D8"
CELL_COLOR = "#FFFFFF"
YELLOW_COLOR = "#FFFF54"
BORDER_COLOR = "#000000"
SIGN_COLOR = "#000000"
SIGN_BG = "#D8D8D8"
TEXT_COLOR = "#000000"


def _load_font(size):
    for path in [
        "Arial Bold.ttf", "Arial-Bold.ttf", "ArialBd.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _draw_chevron(draw, cx, cy, size, direction, color=SIGN_COLOR):
    """Dessine un chevron `<`, `>`, `^` ou `v` centré en (cx, cy) avec 2 lignes épaisses."""
    s = size // 2
    w = max(3, size // 4)  # épaisseur du trait
    if direction == '>':
        p1 = (cx - s, cy - s)
        p2 = (cx + s // 2, cy)
        p3 = (cx - s, cy + s)
    elif direction == '<':
        p1 = (cx + s, cy - s)
        p2 = (cx - s // 2, cy)
        p3 = (cx + s, cy + s)
    elif direction == 'v':
        p1 = (cx - s, cy - s)
        p2 = (cx, cy + s // 2)
        p3 = (cx + s, cy - s)
    elif direction == '^':
        p1 = (cx - s, cy + s)
        p2 = (cx, cy - s // 2)
        p3 = (cx + s, cy + s)
    else:
        return
    draw.line([p1, p2], fill=color, width=w, joint="curve")
    draw.line([p2, p3], fill=color, width=w, joint="curve")


def draw_fix6(puzzle, base_path="fix6_grid", show_solution=True):
    """Génère les images PNG puzzle + solution."""
    solution = puzzle['solution']
    yellows = puzzle['yellows']
    hints = puzzle['hints']
    h_signs = puzzle['h_signs']
    v_signs = puzzle['v_signs']

    # Proportions
    margin_base = 8
    cell_base = 70
    gap_base = 30  # espace pour les signes entre cases
    pitch_base = cell_base + gap_base
    total_base = margin_base * 2 + pitch_base * (GRID - 1) + cell_base

    scale = TARGET_PX / total_base
    cell = int(cell_base * scale)
    gap = int(gap_base * scale)
    pitch = int(pitch_base * scale)
    margin = int(margin_base * scale)
    border_w = max(2, int(1.5 * scale))
    font_size = int(42 * scale)
    sign_size = int(gap_base * 0.85 * scale)

    img_size = margin * 2 + pitch * (GRID - 1) + cell
    font = _load_font(font_size)
    image_paths = []

    for label, show_vals in [("solution", True), ("puzzle", False)]:
        path = f"{base_path}_{label}.png"
        img = Image.new("RGB", (img_size, img_size), BG_COLOR)
        draw = ImageDraw.Draw(img)

        def cell_topleft(r, c):
            return (margin + c * pitch, margin + r * pitch)

        # Cases
        for r in range(GRID):
            for c in range(GRID):
                x, y = cell_topleft(r, c)
                bg = YELLOW_COLOR if yellows[r][c] else CELL_COLOR
                draw.rectangle([x, y, x + cell, y + cell],
                               fill=bg, outline=BORDER_COLOR, width=border_w)
                val = solution[r][c] if show_vals else hints[r][c]
                if val and val != 0:
                    text = str(val)
                    bbox = draw.textbbox((0, 0), text, font=font)
                    tw = bbox[2] - bbox[0]
                    th = bbox[3] - bbox[1]
                    tx = x + (cell - tw) // 2 - bbox[0]
                    ty = y + (cell - th) // 2 - bbox[1]
                    draw.text((tx, ty), text, fill=TEXT_COLOR, font=font)

        # Signes horizontaux (entre (r,c) et (r,c+1))
        for r in range(GRID):
            for c in range(GRID - 1):
                x, y = cell_topleft(r, c)
                cx = x + cell + gap // 2
                cy = y + cell // 2
                _draw_chevron(draw, cx, cy, sign_size, h_signs[r][c])

        # Signes verticaux (entre (r,c) et (r+1,c))
        for r in range(GRID - 1):
            for c in range(GRID):
                x, y = cell_topleft(r, c)
                cx = x + cell // 2
                cy = y + cell + gap // 2
                _draw_chevron(draw, cx, cy, sign_size, v_signs[r][c])

        # Bordure extérieure
        draw.rectangle([(0, 0), (img_size - 1, img_size - 1)],
                       outline=BORDER_COLOR, width=max(1, int(2 * scale)))

        img.save(path)
        image_paths.append(path)
        vis = "solution" if show_vals else "puzzle"
        print(f"Image '{vis}' générée : {path}")

    return image_paths
