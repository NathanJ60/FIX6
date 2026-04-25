#!/usr/bin/env python3
"""Génère 10 FIX-6 avec indices (5-8 aléatoires) + 10 sans indices."""

import os
import random
import time

from fix6_model import generate_puzzle, verify_puzzle, _effective_row_col_unique, GRID
from fix6_visualization import draw_fix6
from check_unique_fix6 import check_uniqueness as cp_sat_check_uniqueness


def run(out_dir: str = "output", n: int = 10):
    os.makedirs(out_dir, exist_ok=True)
    total_start = time.time()
    results = []

    # ========== 10 avec indices (5-8 aléatoires) ==========
    print(f"\n=== {n} grilles AVEC indices (5-8) ===")
    for i in range(n):
        target = random.randint(5, 8)
        t0 = time.time()
        p = generate_puzzle(
            target_hints=target,
            enforce_unique_history=True,
            max_attempts=150,
        )
        dt = time.time() - t0
        if p is None:
            print(f"  [{i+1:02d}/{n}] ECHEC: Echec (target={target})")
            continue
        valid = verify_puzzle(p)
        unique_eff = _effective_row_col_unique(p["solution"], p["yellows"])
        cp_unique = cp_sat_check_uniqueness(p, timeout=20.0, verbose=False)
        n_hints = sum(1 for r in range(GRID) for c in range(GRID) if p["hints"][r][c] != 0)
        # Rejeter si CP-SAT ne prouve pas l'unicité
        if cp_unique is not True:
            print(f"  [{i+1:02d}] ATTENTION: CP-SAT rejette (unique={cp_unique}), retry...")
            continue
        base = os.path.join(out_dir, f"FIX6_avec_indices_{i+1:02d}")
        draw_fix6(p, base)
        status = "OK:" if (valid and unique_eff) else "ECHEC:"
        print(f"  [{i+1:02d}/{n}] {status} {n_hints} indices - {dt:.1f}s")
        results.append(("avec", i + 1, n_hints, valid and unique_eff))

    # ========== 10 sans indices ==========
    print(f"\n=== {n} grilles SANS indices ===")
    for i in range(n):
        t0 = time.time()
        p = generate_puzzle(
            target_hints=0,
            enforce_unique_history=True,
            max_attempts=300,
        )
        dt = time.time() - t0
        if p is None:
            print(f"  [{i+1:02d}/{n}] ECHEC: Echec (sans indices)")
            continue
        valid = verify_puzzle(p)
        unique_eff = _effective_row_col_unique(p["solution"], p["yellows"])
        cp_unique = cp_sat_check_uniqueness(p, timeout=20.0, verbose=False)
        n_hints = sum(1 for r in range(GRID) for c in range(GRID) if p["hints"][r][c] != 0)
        # Rejeter si CP-SAT ne prouve pas l'unicité
        if cp_unique is not True:
            print(f"  [{i+1:02d}] ATTENTION: CP-SAT rejette (unique={cp_unique}), retry...")
            continue
        base = os.path.join(out_dir, f"FIX6_sans_indices_{i+1:02d}")
        draw_fix6(p, base)
        status = "OK:" if (valid and unique_eff and n_hints == 0) else "ECHEC:"
        print(f"  [{i+1:02d}/{n}] {status} {n_hints} indices - {dt:.1f}s")
        results.append(("sans", i + 1, n_hints, valid and unique_eff and n_hints == 0))

    total_dt = time.time() - total_start
    print(f"\n=== BILAN : {len(results)}/{2 * n} en {total_dt:.1f}s ===")
    valid_count = sum(1 for r in results if r[3])
    print(f"  Valides : {valid_count}/{len(results)}")
    print(f"  Fichiers dans {out_dir}/")


if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    run(n=n)
