# FIX-6

Générateur de puzzles FIX-6 : une grille 6×6 à résoudre à l'aide de signes d'inégalité.

## Règles

- Grille 6×6, placer les chiffres 1 à 6.
- Chaque chiffre doit apparaître **une seule fois par ligne et par colonne** (carré latin).
- Entre chaque paire de cases adjacentes se trouve un signe `<`, `>`, `^` ou `v` qui compare les deux valeurs.
- **Une case jaune double la valeur** du chiffre qu'elle contient pour la comparaison (un `2` jaune vaut `4` face à ses voisins).

## Fichiers

- `fix6_model.py` — Générateur : carré latin, placement des cases jaunes, calcul des signes, solveur d'unicité par backtracking.
- `fix6_model_history.py` — Historique persistant hash-based (évite les doublons entre générations).
- `fix6_visualization.py` — Rendu PNG (grille + signes + indices).
- `fix6_gui.py` — Interface PyQt5.

## Utilisation

```bash
python -m venv venv
source venv/bin/activate
pip install PyQt5 Pillow
python fix6_gui.py
```

Ou en ligne de commande :

```python
from fix6_model import generate_puzzle
from fix6_visualization import draw_fix6

puzzle = generate_puzzle(target_hints=None)  # ou 0, 5, 10...
draw_fix6(puzzle, "mon_puzzle")
```

## Paramètres `generate_puzzle`

- `num_yellows` (défaut 7) — nombre de cases jaunes
- `target_hints` — `None` (minimal), `0` (aucun indice), ou un entier (nombre visé)
- `enforce_unique_history` (défaut `True`) — bloque les doublons entre appels

## Garantie d'unicité

Chaque puzzle retourné a une **solution unique**, vérifiée par un solveur de backtracking (`count_solutions`). Si les contraintes seules ne suffisent pas, le générateur ajoute juste assez d'indices pour garantir l'unicité.
