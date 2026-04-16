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
    """Dessine un chevron épais plein style consigne PDF.

    Hexagone simple non-auto-intersectant : triangle extérieur moins un
    triangle intérieur plus petit. Les deux sommets de l'encoche sont
    placés SUR le bord arrière (pas en décalage interne), ce qui garantit
    un polygone simple.

    Ratios :
      - notch_offset = 0.45·s : distance des sommets d'encoche depuis les
        coins extérieurs le long du bord arrière
      - tip_inset    = 0.65·s : distance du tip intérieur depuis le bord
        arrière (inner tip est à 65% du chemin entre back et outer tip)
    """
    s = size / 2.0
    notch_offset = s * 0.45
    tip_inset = s * 0.65

    if direction == '>':
        # Back edge vertical à gauche (x = cx - s)
        outer_top  = (cx - s, cy - s)
        outer_tip  = (cx + s, cy)
        outer_bot  = (cx - s, cy + s)
        notch_top  = (cx - s, cy - s + notch_offset)
        inner_tip  = (cx - s + tip_inset, cy)
        notch_bot  = (cx - s, cy + s - notch_offset)
        # Ordre CCW simple : outer_top → outer_tip → outer_bot → notch_bot → inner_tip → notch_top → close
        pts = [outer_top, outer_tip, outer_bot, notch_bot, inner_tip, notch_top]

    elif direction == '<':
        # Back edge vertical à droite (x = cx + s)
        outer_top  = (cx + s, cy - s)
        outer_tip  = (cx - s, cy)
        outer_bot  = (cx + s, cy + s)
        notch_top  = (cx + s, cy - s + notch_offset)
        inner_tip  = (cx + s - tip_inset, cy)
        notch_bot  = (cx + s, cy + s - notch_offset)
        pts = [outer_top, outer_tip, outer_bot, notch_bot, inner_tip, notch_top]

    elif direction == 'v':
        # Back edge horizontal en haut (y = cy - s)
        outer_left  = (cx - s, cy - s)
        outer_tip   = (cx, cy + s)
        outer_right = (cx + s, cy - s)
        notch_left  = (cx - s + notch_offset, cy - s)
        inner_tip   = (cx, cy - s + tip_inset)
        notch_right = (cx + s - notch_offset, cy - s)
        pts = [outer_left, outer_tip, outer_right, notch_right, inner_tip, notch_left]

    elif direction == '^':
        # Back edge horizontal en bas (y = cy + s)
        outer_left  = (cx - s, cy + s)
        outer_tip   = (cx, cy - s)
        outer_right = (cx + s, cy + s)
        notch_left  = (cx - s + notch_offset, cy + s)
        inner_tip   = (cx, cy + s - tip_inset)
        notch_right = (cx + s - notch_offset, cy + s)
        pts = [outer_left, outer_tip, outer_right, notch_right, inner_tip, notch_left]
    else:
        return

    pts_int = [(int(round(x)), int(round(y))) for (x, y) in pts]
    draw.polygon(pts_int, fill=color)


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
    sign_size = int(gap_base * 0.70 * scale)

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
