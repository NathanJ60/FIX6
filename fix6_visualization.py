#!/usr/bin/env python3
"""fix6_visualization.py - Rendu PNG par PATCHWORK des sprites du gabarit."""

from PIL import Image, ImageDraw, ImageFont
import os

from fix6_model import GRID

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "design", "sprites")

BG_COLOR     = (218, 218, 218)   # gris clair (fond fix6_exemple_1)
TEXT_COLOR   = (0, 0, 0)
OUTER_BORDER = (0, 0, 0)         # cadre extérieur noir simple

# Layout : tiles uniformes (comme la référence où case et chevron+cadre
# ont des largeurs ≈ 90% l'une de l'autre). Les sprites sont préservés
# en ratio et centrés dans une tile carrée → le cadre déco du chevron
# reste lisible et les cases gardent une vraie présence.
TILE      = 240
MARGIN    = 32

# Alias pour rétrocompatibilité dans le reste du module
TILE_CASE = TILE
TILE_CHEV = TILE


def _load_font(size):
    """Arial Bold (même police que 8GO)."""
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


_SPRITES_CACHE = None


def _fit_sprite(sprite, target_w, target_h, bg=BG_COLOR):
    """Redimensionne un sprite en préservant son ratio et le centre dans une
    tile target_w×target_h sur fond beige (pas de déformation)."""
    sw, sh = sprite.size
    # Échelle qui fait rentrer le sprite dans la tile en gardant le ratio
    scale = min(target_w / sw, target_h / sh)
    new_w = max(1, int(sw * scale))
    new_h = max(1, int(sh * scale))
    resized = sprite.resize((new_w, new_h), Image.LANCZOS)
    tile = Image.new("RGB", (target_w, target_h), bg)
    ox = (target_w - new_w) // 2
    oy = (target_h - new_h) // 2
    tile.paste(resized, (ox, oy))
    return tile


def _load_sprites():
    """Charge et prépare les 6 sprites aux bonnes tailles."""
    global _SPRITES_CACHE
    if _SPRITES_CACHE is not None:
        return _SPRITES_CACHE
    raw = {}
    for name in ("case_white", "case_yellow",
                 "chev_right", "chev_left", "chev_up", "chev_down"):
        p = os.path.join(ASSETS, f"{name}.png")
        raw[name] = Image.open(p).convert("RGB")

    # Cases : tile carrée TILE_CASE × TILE_CASE
    sprites = {
        "case_white":  _fit_sprite(raw["case_white"],  TILE_CASE, TILE_CASE),
        "case_yellow": _fit_sprite(raw["case_yellow"], TILE_CASE, TILE_CASE),
        # Chevrons H : tile rectangulaire TILE_CHEV (large) × TILE_CASE (haut)
        "chev_right":  _fit_sprite(raw["chev_right"],  TILE_CHEV, TILE_CASE),
        "chev_left":   _fit_sprite(raw["chev_left"],   TILE_CHEV, TILE_CASE),
        # Chevrons V : tile rectangulaire TILE_CASE (large) × TILE_CHEV (haut)
        "chev_up":     _fit_sprite(raw["chev_up"],     TILE_CASE, TILE_CHEV),
        "chev_down":   _fit_sprite(raw["chev_down"],   TILE_CASE, TILE_CHEV),
    }
    _SPRITES_CACHE = sprites
    return sprites


def draw_fix6(puzzle, base_path="fix6_grid", show_solution=True):
    solution = puzzle['solution']
    yellows  = puzzle['yellows']
    hints    = puzzle['hints']
    h_signs  = puzzle['h_signs']
    v_signs  = puzzle['v_signs']

    sprites = _load_sprites()

    # Dimensions globales
    cells_w = GRID * TILE_CASE + (GRID - 1) * TILE_CHEV
    img_size = cells_w + 2 * MARGIN

    # Police : Arial Bold, taille proportionnelle
    font = _load_font(int(TILE_CASE * 0.55))
    image_paths = []

    # Coordonnées des origines des cellules (cases) et chevrons
    def case_origin(r, c):
        x = MARGIN + c * (TILE_CASE + TILE_CHEV)
        y = MARGIN + r * (TILE_CASE + TILE_CHEV)
        return x, y

    def chev_h_origin(r, c):
        # Chevron horizontal entre cases (r, c) et (r, c+1)
        x = MARGIN + c * (TILE_CASE + TILE_CHEV) + TILE_CASE
        y = MARGIN + r * (TILE_CASE + TILE_CHEV)
        return x, y

    def chev_v_origin(r, c):
        # Chevron vertical entre cases (r, c) et (r+1, c)
        x = MARGIN + c * (TILE_CASE + TILE_CHEV)
        y = MARGIN + r * (TILE_CASE + TILE_CHEV) + TILE_CASE
        return x, y

    for label, show_vals in [("solution", True), ("puzzle", False)]:
        path = f"{base_path}_{label}.png"
        img = Image.new("RGB", (img_size, img_size), BG_COLOR)

        # 1) Cases
        for r in range(GRID):
            for c in range(GRID):
                x, y = case_origin(r, c)
                spr = sprites["case_yellow"] if yellows[r][c] else sprites["case_white"]
                img.paste(spr, (x, y))

        # 2) Chevrons horizontaux
        for r in range(GRID):
            for c in range(GRID - 1):
                x, y = chev_h_origin(r, c)
                spr = sprites["chev_right"] if h_signs[r][c] == '>' else sprites["chev_left"]
                img.paste(spr, (x, y))

        # 3) Chevrons verticaux
        for r in range(GRID - 1):
            for c in range(GRID):
                x, y = chev_v_origin(r, c)
                spr = sprites["chev_down"] if v_signs[r][c] == 'v' else sprites["chev_up"]
                img.paste(spr, (x, y))

        # 4) Chiffres centrés (anchor="mm" = milieu visuel)
        draw = ImageDraw.Draw(img)
        for r in range(GRID):
            for c in range(GRID):
                val = solution[r][c] if show_vals else hints[r][c]
                if not val:
                    continue
                x, y = case_origin(r, c)
                cx = x + TILE_CASE // 2
                cy = y + TILE_CASE // 2
                draw.text((cx, cy), str(val),
                          fill=TEXT_COLOR, font=font, anchor="mm")

        # 5) Cadre extérieur marine
        outer_w = max(3, TILE_CASE // 60)
        for k in range(outer_w):
            draw.rectangle([k, k, img_size - 1 - k, img_size - 1 - k],
                           outline=OUTER_BORDER)

        img.save(path)
        image_paths.append(path)
        vis = "solution" if show_vals else "puzzle"
        print(f"Image '{vis}' générée : {path}")

    return image_paths
