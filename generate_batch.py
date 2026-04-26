#!/usr/bin/env python3
"""Génère N grilles FIX-6 par niveau et écrit les PNG dans output/.

Usage:
    python3 generate_batch.py [n_per_level]

  n_per_level    nombre de grilles par niveau (défaut 5)

Niveaux générés (5) :
  - tres_facile  : 15 indices
  - facile       : 8-10 indices
  - moyen        : 5-8 indices
  - difficile    : 1-3 indices
  - sans_indices : 0 indice
"""

import os
import sys
import time

from fix6_model import generate_puzzle_at_level, verify_puzzle, _effective_row_col_unique, GRID
from fix6_visualization import draw_fix6
from check_unique_fix6 import check_uniqueness as cp_sat_check_uniqueness


LEVELS = ["tres_facile", "facile", "moyen", "difficile", "sans_indices"]


def run(out_dir: str = "output", n: int = 5):
    os.makedirs(out_dir, exist_ok=True)
    total_start = time.time()
    results = []

    for level in LEVELS:
        print(f"\n=== Niveau {level} : {n} grilles ===")
        for i in range(n):
            t0 = time.time()
            p = generate_puzzle_at_level(difficulty=level, enforce_unique_history=True,
                                         max_attempts=300)
            dt = time.time() - t0
            if p is None:
                print(f"  [{i+1:02d}/{n}] ECHEC: niveau={level}")
                continue
            valid = verify_puzzle(p)
            unique_eff = _effective_row_col_unique(p["solution"], p["yellows"])
            cp_unique = cp_sat_check_uniqueness(p, timeout=20.0, verbose=False)
            n_hints = sum(1 for r in range(GRID) for c in range(GRID) if p["hints"][r][c] != 0)
            if cp_unique is not True:
                print(f"  [{i+1:02d}/{n}] ATTENTION: CP-SAT rejette (unique={cp_unique}), retry...")
                continue
            base = os.path.join(out_dir, f"FIX6_{level}_{i+1:02d}")
            draw_fix6(p, base)
            status = "OK:" if (valid and unique_eff) else "ECHEC:"
            print(f"  [{i+1:02d}/{n}] {status} {n_hints} indices - {dt:.1f}s")
            results.append((level, i + 1, n_hints, valid and unique_eff))

    total_dt = time.time() - total_start
    valid_count = sum(1 for r in results if r[3])
    print(f"\n=== BILAN : {valid_count}/{len(results)} valides en {total_dt:.1f}s ===")
    print(f"  Fichiers dans {out_dir}/")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    run(n=n)
