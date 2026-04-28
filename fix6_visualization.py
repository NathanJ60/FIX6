#!/usr/bin/env python3
"""fix6_visualization.py - Rendu FIX-6 (PNG par sprites + SVG/PDF vectoriels)."""

from PIL import Image, ImageDraw, ImageFont
import os
import sys

from fix6_model import GRID

# Determiner le dossier de base (fonctionne avec PyInstaller)
if getattr(sys, 'frozen', False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    import svgwrite
    SVG_AVAILABLE = True
except ImportError:
    SVG_AVAILABLE = False

try:
    from reportlab.pdfgen import canvas as _pdf_canvas
    from reportlab.lib.colors import HexColor
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

ASSETS = os.path.join(_BASE_DIR, "design", "sprites")

BG_COLOR     = (218, 218, 218)   # gris clair (fond fix6_exemple_1)
TEXT_COLOR   = (0, 0, 0)
OUTER_BORDER = (0, 0, 0)         # cadre extérieur noir simple

# Couleurs vectorielles (SVG/PDF) — palette equivalente aux sprites
BG_HEX     = "#DADADA"
WHITE_HEX  = "#FFFFFF"
YELLOW_HEX = "#FFFF54"
BORDER_HEX = "#000000"
TEXT_HEX   = "#000000"

TARGET_CM = 12  # Taille physique cible pour SVG/PDF

# Layout : tiles uniformes (comme la référence où case et chevron+cadre
# ont des largeurs ≈ 90% l'une de l'autre). Les sprites sont préservés
# en ratio et centrés dans une tile carrée -> le cadre déco du chevron
# reste lisible et les cases gardent une vraie présence.
TILE      = 240
MARGIN    = 32

# Alias pour rétrocompatibilité dans le reste du module
TILE_CASE = TILE
TILE_CHEV = TILE


def _load_font(size):
    """Charge Arial Bold (Windows, macOS, Linux)."""
    for path in [
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Bold.ttf",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "Arial Bold.ttf", "Arial-Bold.ttf", "ArialBd.ttf",
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
        print(f"Image '{vis}' generee : {path}")

    return image_paths


# =============================================================================
# Layout vectoriel partage (SVG / PDF)
# =============================================================================

def _vector_layout():
    """Unites de base pour les rendus vectoriels (mm-like, scalees a 12 cm)."""
    cell = 80           # case carree
    chev = 80           # tile chevron carree
    margin = 12
    total = 2 * margin + GRID * cell + (GRID - 1) * chev
    return cell, chev, margin, total


def _case_xy(r, c, cell, chev, margin):
    x = margin + c * (cell + chev)
    y = margin + r * (cell + chev)
    return x, y


def _chev_h_xy(r, c, cell, chev, margin):
    x = margin + c * (cell + chev) + cell
    y = margin + r * (cell + chev)
    return x, y


def _chev_v_xy(r, c, cell, chev, margin):
    x = margin + c * (cell + chev)
    y = margin + r * (cell + chev) + cell
    return x, y


def _chev_polygon(kind, ox, oy, w, h, inset=0.22):
    """Coordonnees d'un triangle plein representant le chevron.

    kind: 'right' (>), 'left' (<), 'up' (^), 'down' (v).
    Retourne une liste de tuples (x, y).
    """
    pad_x = w * inset
    pad_y = h * inset
    x0, y0 = ox + pad_x, oy + pad_y
    x1, y1 = ox + w - pad_x, oy + h - pad_y
    cx, cy = ox + w / 2, oy + h / 2
    if kind == 'right':
        return [(x0, y0), (x1, cy), (x0, y1)]
    if kind == 'left':
        return [(x1, y0), (x0, cy), (x1, y1)]
    if kind == 'up':
        return [(x0, y1), (cx, y0), (x1, y1)]
    # down
    return [(x0, y0), (cx, y1), (x1, y0)]


# =============================================================================
# SVG
# =============================================================================

def draw_fix6_svg(puzzle, base_path="fix6_grid"):
    """Genere les SVG puzzle + solution. Necessite svgwrite."""
    if not SVG_AVAILABLE:
        raise ImportError("svgwrite non installe")

    solution = puzzle['solution']
    yellows  = puzzle['yellows']
    hints    = puzzle['hints']
    h_signs  = puzzle['h_signs']
    v_signs  = puzzle['v_signs']

    cell, chev, margin, total = _vector_layout()
    border_w = 2
    outer_w = 4
    font_size = int(cell * 0.55)

    image_paths = []
    for label, show_vals in [("solution", True), ("puzzle", False)]:
        path = f"{base_path}_{label}.svg"
        dwg = svgwrite.Drawing(
            path,
            size=(f"{TARGET_CM}cm", f"{TARGET_CM}cm"),
            viewBox=f"0 0 {total} {total}",
        )
        dwg.add(dwg.rect(insert=(0, 0), size=(total, total), fill=BG_HEX))

        # Cases
        for r in range(GRID):
            for c in range(GRID):
                x, y = _case_xy(r, c, cell, chev, margin)
                fill = YELLOW_HEX if yellows[r][c] else WHITE_HEX
                dwg.add(dwg.rect(insert=(x, y), size=(cell, cell),
                                 fill=fill, stroke=BORDER_HEX, stroke_width=border_w))
                val = solution[r][c] if show_vals else hints[r][c]
                if val:
                    dwg.add(dwg.text(
                        str(val),
                        insert=(x + cell / 2, y + cell / 2 + font_size / 3),
                        text_anchor="middle",
                        font_family="Helvetica, Arial, sans-serif",
                        font_size=f"{font_size}px",
                        font_weight="bold",
                        fill=TEXT_HEX,
                    ))

        # Chevrons horizontaux
        for r in range(GRID):
            for c in range(GRID - 1):
                ox, oy = _chev_h_xy(r, c, cell, chev, margin)
                kind = 'right' if h_signs[r][c] == '>' else 'left'
                pts = _chev_polygon(kind, ox, oy, chev, cell)
                dwg.add(dwg.polygon(points=pts, fill=BORDER_HEX,
                                    stroke=BORDER_HEX, stroke_width=1))

        # Chevrons verticaux
        for r in range(GRID - 1):
            for c in range(GRID):
                ox, oy = _chev_v_xy(r, c, cell, chev, margin)
                kind = 'down' if v_signs[r][c] == 'v' else 'up'
                pts = _chev_polygon(kind, ox, oy, cell, chev)
                dwg.add(dwg.polygon(points=pts, fill=BORDER_HEX,
                                    stroke=BORDER_HEX, stroke_width=1))

        # Cadre exterieur
        dwg.add(dwg.rect(insert=(0, 0), size=(total, total),
                         fill="none", stroke=BORDER_HEX, stroke_width=outer_w))
        dwg.save()
        image_paths.append(path)
        print(f"SVG '{label}' genere : {path}")

    return image_paths


# =============================================================================
# PDF
# =============================================================================

def draw_fix6_pdf(puzzle, base_path="fix6_grid"):
    """Genere les PDF puzzle + solution. Necessite reportlab."""
    if not PDF_AVAILABLE:
        raise ImportError("reportlab non installe")

    solution = puzzle['solution']
    yellows  = puzzle['yellows']
    hints    = puzzle['hints']
    h_signs  = puzzle['h_signs']
    v_signs  = puzzle['v_signs']

    cell_base, chev_base, margin_base, total_base = _vector_layout()
    target_size = TARGET_CM * 28.35  # cm -> pt
    s = target_size / total_base
    cell = cell_base * s
    chev = chev_base * s
    margin = margin_base * s
    size = target_size
    font_size = cell * 0.55
    border_w = 2 * s
    outer_w = 4 * s

    image_paths = []
    for label, show_vals in [("solution", True), ("puzzle", False)]:
        path = f"{base_path}_{label}.pdf"
        c = _pdf_canvas.Canvas(path, pagesize=(size, size))

        # Fond
        c.setFillColor(HexColor(BG_HEX))
        c.rect(0, 0, size, size, fill=1, stroke=0)

        # Cases
        for r in range(GRID):
            for ci in range(GRID):
                x = margin + ci * (cell + chev)
                # ReportLab Y croit vers le haut
                y = size - (margin + r * (cell + chev) + cell)
                fill = YELLOW_HEX if yellows[r][ci] else WHITE_HEX
                c.setFillColor(HexColor(fill))
                c.setStrokeColor(HexColor(BORDER_HEX))
                c.setLineWidth(border_w)
                c.rect(x, y, cell, cell, fill=1, stroke=1)
                val = solution[r][ci] if show_vals else hints[r][ci]
                if val:
                    t = str(val)
                    c.setFillColor(HexColor(TEXT_HEX))
                    c.setFont("Helvetica-Bold", font_size)
                    tw = c.stringWidth(t, "Helvetica-Bold", font_size)
                    c.drawString(x + (cell - tw) / 2,
                                 y + cell / 2 - font_size / 3, t)

        def _draw_polygon_pdf(pts):
            p = c.beginPath()
            p.moveTo(*pts[0])
            for px, py in pts[1:]:
                p.lineTo(px, py)
            p.close()
            c.setFillColor(HexColor(BORDER_HEX))
            c.setStrokeColor(HexColor(BORDER_HEX))
            c.drawPath(p, fill=1, stroke=1)

        # Chevrons horizontaux
        for r in range(GRID):
            for ci in range(GRID - 1):
                ox = margin + ci * (cell + chev) + cell
                oy_top = margin + r * (cell + chev)
                oy = size - (oy_top + cell)
                kind = 'right' if h_signs[r][ci] == '>' else 'left'
                # _chev_polygon attend coords ecran (Y vers le bas) ; on flippe en PDF
                pts_top = _chev_polygon(kind, ox, oy_top, chev, cell)
                pts_pdf = [(px, size - py) for (px, py) in pts_top]
                _draw_polygon_pdf(pts_pdf)

        # Chevrons verticaux
        for r in range(GRID - 1):
            for ci in range(GRID):
                ox = margin + ci * (cell + chev)
                oy_top = margin + r * (cell + chev) + cell
                kind = 'down' if v_signs[r][ci] == 'v' else 'up'
                pts_top = _chev_polygon(kind, ox, oy_top, cell, chev)
                pts_pdf = [(px, size - py) for (px, py) in pts_top]
                _draw_polygon_pdf(pts_pdf)

        # Cadre exterieur
        c.setStrokeColor(HexColor(BORDER_HEX))
        c.setLineWidth(outer_w)
        c.rect(0, 0, size, size, fill=0, stroke=1)

        c.save()
        image_paths.append(path)
        print(f"PDF '{label}' genere : {path}")

    return image_paths
