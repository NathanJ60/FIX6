#!/usr/bin/env python3
"""Vérification stricte d'unicité pour FIX-6 via CP-SAT (OR-Tools).

Approche (identique à check_unique_go8.py) :
- Phase 1 : construire un modèle CP-SAT avec toutes les contraintes (latin square,
  jaunes, signes, indices) et trouver une solution.
- Phase 2 : interdire cette solution et chercher une seconde. Si INFEASIBLE -> unique.

Retourne True ssi le solveur PROUVE qu'il n'existe qu'une seule solution.
"""

from ortools.sat.python import cp_model
import time

from fix6_model import GRID, DIGITS, effective


def build_fix6_model(yellows, h_signs, v_signs, hints):
    """Construit un modèle CP-SAT complet pour FIX-6."""
    model = cp_model.CpModel()

    # Variables : chiffre écrit dans chaque case (1..6)
    V = [[model.NewIntVar(1, GRID, f"V_{r}_{c}") for c in range(GRID)] for r in range(GRID)]

    # Variables : valeur effective (= 2*V si jaune, sinon = V)
    E = [[None] * GRID for _ in range(GRID)]
    for r in range(GRID):
        for c in range(GRID):
            e = model.NewIntVar(1, 2 * GRID, f"E_{r}_{c}")
            if yellows[r][c]:
                model.Add(e == 2 * V[r][c])
            else:
                model.Add(e == V[r][c])
            E[r][c] = e

    # Latin square : AllDifferent sur chiffres écrits par ligne et colonne
    for r in range(GRID):
        model.AddAllDifferent([V[r][c] for c in range(GRID)])
    for c in range(GRID):
        model.AddAllDifferent([V[r][c] for r in range(GRID)])

    # Unicité des valeurs effectives par ligne et colonne (contrainte supplémentaire)
    for r in range(GRID):
        model.AddAllDifferent([E[r][c] for c in range(GRID)])
    for c in range(GRID):
        model.AddAllDifferent([E[r][c] for r in range(GRID)])

    # Signes horizontaux
    for r in range(GRID):
        for c in range(GRID - 1):
            sign = h_signs[r][c]
            if sign == '<':
                model.Add(E[r][c] < E[r][c + 1])
            elif sign == '>':
                model.Add(E[r][c] > E[r][c + 1])

    # Signes verticaux (convention : v = top > bot, ^ = top < bot)
    for r in range(GRID - 1):
        for c in range(GRID):
            sign = v_signs[r][c]
            if sign == 'v':
                model.Add(E[r][c] > E[r + 1][c])
            elif sign == '^':
                model.Add(E[r][c] < E[r + 1][c])

    # Indices visibles : fixer les valeurs connues
    for r in range(GRID):
        for c in range(GRID):
            if hints[r][c] != 0:
                model.Add(V[r][c] == hints[r][c])

    return model, V


def forbid_solution(model, V, solution):
    """Ajoute une clause interdisant la solution donnée."""
    diff_bools = []
    for r in range(GRID):
        for c in range(GRID):
            b = model.NewBoolVar(f"d_{r}_{c}")
            model.Add(V[r][c] != solution[r][c]).OnlyEnforceIf(b)
            model.Add(V[r][c] == solution[r][c]).OnlyEnforceIf(b.Not())
            diff_bools.append(b)
    model.Add(sum(diff_bools) >= 1)


def check_uniqueness(puzzle, timeout: float = 30.0, verbose: bool = False):
    """Retourne True si le puzzle a une seule solution (prouvée par CP-SAT).

    Retourne False si 0 ou ≥2 solutions, None en cas de timeout."""
    t0 = time.time()
    yellows = puzzle["yellows"]
    h_signs = puzzle["h_signs"]
    v_signs = puzzle["v_signs"]
    hints = puzzle["hints"]
    original_solution = puzzle.get("solution")

    # Phase 1 : trouver une solution
    model1, V1 = build_fix6_model(yellows, h_signs, v_signs, hints)
    solver1 = cp_model.CpSolver()
    solver1.parameters.max_time_in_seconds = timeout / 2
    solver1.parameters.num_search_workers = 8
    status1 = solver1.Solve(model1)
    if status1 not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        if verbose:
            print(f"  [UNICITE] ECHEC: Aucune solution")
        return False

    solution1 = [[solver1.Value(V1[r][c]) for c in range(GRID)] for r in range(GRID)]

    if original_solution is not None:
        matches = all(solution1[r][c] == original_solution[r][c]
                      for r in range(GRID) for c in range(GRID))
        if not matches:
            if verbose:
                print(f"  [UNICITE] ECHEC: Solution CP-SAT differe de l'originale")
            return False

    if verbose:
        print(f"  [UNICITE] OK: Phase 1 OK ({time.time() - t0:.2f}s)")

    # Phase 2 : interdire la solution 1 et chercher une 2e
    model2, V2 = build_fix6_model(yellows, h_signs, v_signs, hints)
    forbid_solution(model2, V2, solution1)
    solver2 = cp_model.CpSolver()
    solver2.parameters.max_time_in_seconds = timeout / 2
    solver2.parameters.num_search_workers = 8
    status2 = solver2.Solve(model2)

    if status2 in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        if verbose:
            # Afficher la 2e solution trouvee
            s2 = [[solver2.Value(V2[r][c]) for c in range(GRID)] for r in range(GRID)]
            print(f"  [UNICITE] ECHEC: 2e solution trouvee -> NON UNIQUE")
            print(f"  Solution 1 : {solution1}")
            print(f"  Solution 2 : {s2}")
        return False

    if status2 == cp_model.UNKNOWN:
        if verbose:
            print(f"  [UNICITE] ? Timeout phase 2")
        return None

    if verbose:
        print(f"  [UNICITE] OK: UNIQUE (prouvé en {time.time() - t0:.2f}s)")
    return True


if __name__ == "__main__":
    from fix6_model import generate_puzzle

    print("Test CP-SAT uniqueness sur 20 grilles FIX-6\n")

    total = 0
    unique = 0
    for i in range(20):
        p = generate_puzzle(target_hints=6, enforce_unique_history=False, max_attempts=100)
        if p is None:
            print(f"[{i+1:02d}] ECHEC: échec génération")
            continue
        total += 1
        result = check_uniqueness(p, timeout=20.0, verbose=False)
        status = "OK: UNIQUE" if result is True else ("ECHEC: NON-UNIQUE" if result is False else "? TIMEOUT")
        print(f"[{i+1:02d}] {status}")
        if result is True:
            unique += 1

    print(f"\n=== BILAN : {unique}/{total} uniques prouvés par CP-SAT ===")
