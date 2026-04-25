#!/usr/bin/env python3
"""fix6_model.py - Generateur de puzzles FIX-6.

Règles:
- Grille 6×6, chiffres 1..6, chaque chiffre une seule fois par ligne et par colonne.
- Entre chaque paire de cases adjacentes (horizontale et verticale), un signe
  d'inégalité < > ^ v compare les valeurs EFFECTIVES des deux cases.
- Une case jaune double la valeur du chiffre qu'elle contient (effective = 2*val).
- Le puzzle affiche quelques indices; la solution doit être unique.
"""

import random
from typing import List, Tuple, Optional

from fix6_model_history import is_unique as hist_unique, add_to_history

GRID = 6
DIGITS = list(range(1, GRID + 1))


def effective(value: int, yellow: bool) -> int:
    """Valeur effective (doublée si case jaune)."""
    return value * 2 if yellow else value


def _random_latin_square(size: int = GRID) -> List[List[int]]:
    """Génère un carré latin aléatoire par backtracking."""
    grid = [[0] * size for _ in range(size)]

    def backtrack(idx: int) -> bool:
        if idx == size * size:
            return True
        r, c = divmod(idx, size)
        digits = DIGITS[:]
        random.shuffle(digits)
        for d in digits:
            if any(grid[r][cc] == d for cc in range(c)):
                continue
            if any(grid[rr][c] == d for rr in range(r)):
                continue
            grid[r][c] = d
            if backtrack(idx + 1):
                return True
            grid[r][c] = 0
        return False

    backtrack(0)
    return grid


def _compute_signs(solution, yellows):
    """À partir de la solution et des cases jaunes, calcule tous les signes.

    Retourne (h_signs, v_signs, ok) où ok=False si deux cases adjacentes ont
    la même valeur effective (aucune inégalité stricte possible).
    """
    h = [[None] * (GRID - 1) for _ in range(GRID)]
    v = [[None] * GRID for _ in range(GRID - 1)]
    for r in range(GRID):
        for c in range(GRID - 1):
            a = effective(solution[r][c], yellows[r][c])
            b = effective(solution[r][c + 1], yellows[r][c + 1])
            if a == b:
                return None, None, False
            h[r][c] = '<' if a < b else '>'
    for r in range(GRID - 1):
        for c in range(GRID):
            a = effective(solution[r][c], yellows[r][c])
            b = effective(solution[r + 1][c], yellows[r + 1][c])
            if a == b:
                return None, None, False
            # Convention visuelle : 'v' (point en bas) = top > bottom ;
            # '^' (point en haut) = top < bottom
            v[r][c] = 'v' if a > b else '^'
    return h, v, True


def _place_yellows(num_yellows: int = 7) -> List[List[bool]]:
    """Place aléatoirement `num_yellows` cases jaunes."""
    cells = [(r, c) for r in range(GRID) for c in range(GRID)]
    random.shuffle(cells)
    yellows = [[False] * GRID for _ in range(GRID)]
    for r, c in cells[:num_yellows]:
        yellows[r][c] = True
    return yellows


def _effective_row_col_unique(solution, yellows) -> bool:
    """Vérifie que les valeurs EFFECTIVES (après doublement jaune) sont uniques
    par ligne ET par colonne. Évite les chaînes de comparaison visuellement
    incohérentes (ex: ligne avec deux cases à valeur effective 6).
    """
    for r in range(GRID):
        effs = [effective(solution[r][c], yellows[r][c]) for c in range(GRID)]
        if len(set(effs)) != GRID:
            return False
    for c in range(GRID):
        effs = [effective(solution[r][c], yellows[r][c]) for r in range(GRID)]
        if len(set(effs)) != GRID:
            return False
    return True


def count_solutions(hints, yellows, h_signs, v_signs, limit=2):
    """Backtracking: compte les solutions jusqu'à `limit`. Retourne le nombre."""
    grid = [row[:] for row in hints]

    def row_ok(r, c, d):
        return all(grid[r][cc] != d for cc in range(GRID) if cc != c)

    def col_ok(r, c, d):
        return all(grid[rr][c] != d for rr in range(GRID) if rr != r)

    def signs_ok(r, c, d):
        eff = effective(d, yellows[r][c])
        # Gauche
        if c > 0 and grid[r][c - 1] != 0:
            le = effective(grid[r][c - 1], yellows[r][c - 1])
            sign = h_signs[r][c - 1]
            if sign == '<' and not (le < eff):
                return False
            if sign == '>' and not (le > eff):
                return False
        # Droite
        if c < GRID - 1 and grid[r][c + 1] != 0:
            ri = effective(grid[r][c + 1], yellows[r][c + 1])
            sign = h_signs[r][c]
            if sign == '<' and not (eff < ri):
                return False
            if sign == '>' and not (eff > ri):
                return False
        # Haut (sign entre r-1 (top) et r (current bottom))
        # Nouvelle convention : 'v' = top > bottom, '^' = top < bottom
        if r > 0 and grid[r - 1][c] != 0:
            up = effective(grid[r - 1][c], yellows[r - 1][c])
            sign = v_signs[r - 1][c]
            if sign == 'v' and not (up > eff):
                return False
            if sign == '^' and not (up < eff):
                return False
        # Bas (sign entre r (current top) et r+1 (bottom))
        if r < GRID - 1 and grid[r + 1][c] != 0:
            dn = effective(grid[r + 1][c], yellows[r + 1][c])
            sign = v_signs[r][c]
            if sign == 'v' and not (eff > dn):
                return False
            if sign == '^' and not (eff < dn):
                return False
        return True

    count = [0]

    def bt(idx=0):
        if count[0] >= limit:
            return
        if idx == GRID * GRID:
            count[0] += 1
            return
        r, c = divmod(idx, GRID)
        if grid[r][c] != 0:
            bt(idx + 1)
            return
        for d in DIGITS:
            if not row_ok(r, c, d):
                continue
            if not col_ok(r, c, d):
                continue
            grid[r][c] = d
            if signs_ok(r, c, d):
                bt(idx + 1)
            grid[r][c] = 0
            if count[0] >= limit:
                return

    bt(0)
    return count[0]


def _build_hints(solution, yellows, h_signs, v_signs, target_hints=None):
    """Construit un jeu d'indices qui garantit l'unicité de la solution.

    target_hints:
      - None  : cherche un jeu minimal (peut être 0)
      - int N : essaye d'avoir exactement N indices (>= minimum nécessaire)
    Retourne les hints ou None si impossible (ex: N < minimum nécessaire).
    """
    cells = [(r, c) for r in range(GRID) for c in range(GRID)]

    # Cas spécial : 0 indice - verifier si les contraintes suffisent
    hints = [[0] * GRID for _ in range(GRID)]
    n_sol = count_solutions(hints, yellows, h_signs, v_signs, limit=2)
    if n_sol == 1:
        if target_hints is None or target_hints == 0:
            return hints
        # On veut plus d'indices : en ajouter
        random.shuffle(cells)
        added = 0
        for r, c in cells:
            if added >= target_hints:
                break
            hints[r][c] = solution[r][c]
            added += 1
        return hints

    # Sinon il faut des indices. On en ajoute jusqu'à l'unicité.
    random.shuffle(cells)
    idx = 0
    while count_solutions(hints, yellows, h_signs, v_signs, limit=2) > 1:
        if idx >= len(cells):
            return None
        r, c = cells[idx]
        hints[r][c] = solution[r][c]
        idx += 1

    # idx = nombre d'indices minimum pour l'unicité sur cet ordre
    min_hints = sum(1 for r in range(GRID) for c in range(GRID) if hints[r][c] != 0)

    if target_hints is None:
        # Minimiser : essayer de retirer des indices tant que ça reste unique
        order = [(r, c) for r in range(GRID) for c in range(GRID) if hints[r][c] != 0]
        random.shuffle(order)
        for r, c in order:
            backup = hints[r][c]
            hints[r][c] = 0
            if count_solutions(hints, yellows, h_signs, v_signs, limit=2) != 1:
                hints[r][c] = backup
        return hints

    if target_hints < min_hints:
        return None  # Impossible d'avoir moins que le minimum

    # Ajouter des indices pour atteindre target_hints
    empty = [(r, c) for r in range(GRID) for c in range(GRID) if hints[r][c] == 0]
    random.shuffle(empty)
    current = min_hints
    for r, c in empty:
        if current >= target_hints:
            break
        hints[r][c] = solution[r][c]
        current += 1
    return hints


def generate_puzzle(num_yellows: int = 7, target_hints=None,
                    enforce_unique_history: bool = True, max_attempts: int = 80):
    """Génère un puzzle FIX-6 complet avec solution unique.

    num_yellows: nombre de cases jaunes (défaut 7)
    target_hints: None=minimal, 0=aucun indice, int=nombre d'indices visé
    Retourne un dict: {solution, yellows, h_signs, v_signs, hints}.
    """
    for _ in range(max_attempts):
        solution = _random_latin_square()
        # Retry yellow placement : signes stricts + valeurs effectives uniques par ligne/col
        h_signs = v_signs = None
        yellows = None
        for _ in range(100):
            yellows_try = _place_yellows(num_yellows)
            if not _effective_row_col_unique(solution, yellows_try):
                continue
            h_try, v_try, ok = _compute_signs(solution, yellows_try)
            if ok:
                yellows = yellows_try
                h_signs, v_signs = h_try, v_try
                break
        if h_signs is None:
            continue

        hints = _build_hints(solution, yellows, h_signs, v_signs, target_hints)
        if hints is None:
            continue

        if enforce_unique_history and not hist_unique(solution, yellows):
            continue

        puzzle = {
            'solution': solution,
            'yellows': yellows,
            'h_signs': h_signs,
            'v_signs': v_signs,
            'hints': hints,
        }

        if enforce_unique_history:
            num_hints = sum(1 for r in range(GRID) for c in range(GRID) if hints[r][c] != 0)
            add_to_history(solution, yellows, metadata={
                'num_yellows': num_yellows,
                'num_hints': num_hints,
            })

        return puzzle

    return None


def verify_puzzle(puzzle) -> bool:
    """Vérifie la validité du puzzle."""
    sol = puzzle['solution']
    yellows = puzzle['yellows']
    h_signs = puzzle['h_signs']
    v_signs = puzzle['v_signs']
    hints = puzzle['hints']

    # Latin square
    for r in range(GRID):
        if sorted(sol[r]) != DIGITS:
            print(f"ECHEC: Ligne {r}: {sol[r]}")
            return False
    for c in range(GRID):
        col = [sol[r][c] for r in range(GRID)]
        if sorted(col) != DIGITS:
            print(f"ECHEC: Colonne {c}: {col}")
            return False

    # Signes
    hs, vs, ok = _compute_signs(sol, yellows)
    if not ok or hs != h_signs or vs != v_signs:
        print("ECHEC: Signes incohérents avec la solution")
        return False

    # Unicité des valeurs effectives par ligne et colonne
    if not _effective_row_col_unique(sol, yellows):
        print("ECHEC: Doublon de valeur effective sur une ligne ou colonne")
        return False

    # Unicité
    n = count_solutions(hints, yellows, h_signs, v_signs, limit=2)
    if n != 1:
        print(f"ECHEC: {n} solutions trouvees (attendu 1)")
        return False

    print("OK: FIX-6 valide et unique")
    return True


def print_puzzle(puzzle):
    sol = puzzle['solution']
    yellows = puzzle['yellows']
    hints = puzzle['hints']
    h_signs = puzzle['h_signs']
    v_signs = puzzle['v_signs']

    print("\n--- Solution ---")
    for r in range(GRID):
        line = ""
        for c in range(GRID):
            tag = "*" if yellows[r][c] else " "
            line += f"{sol[r][c]}{tag} "
        print(line)

    print("\n--- Indices ---")
    for r in range(GRID):
        line = ""
        for c in range(GRID):
            if hints[r][c] != 0:
                tag = "*" if yellows[r][c] else " "
                line += f"{hints[r][c]}{tag}"
            else:
                line += "_ " if not yellows[r][c] else "_*"
            if c < GRID - 1:
                line += h_signs[r][c]
        print(line)
        if r < GRID - 1:
            print(" " + "  ".join(v_signs[r]))


if __name__ == "__main__":
    print("Generation d'un puzzle FIX-6...")
    p = generate_puzzle(enforce_unique_history=False)
    if p:
        print_puzzle(p)
        verify_puzzle(p)
    else:
        print("ECHEC: Echec")
