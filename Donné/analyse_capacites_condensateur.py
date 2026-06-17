"""
analyse_capacites_condensateur.py
----------------------------------
Analyse de la capacité de condensateurs C1 et C2 en fonction de la distance d.
Les mesures sont répétées sur 3 essais pour évaluer la dispersion expérimentale.
Les figures sont sauvegardées dans le dossier 'Figure/'.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ── Création du dossier de sortie des figures ──────────────────────────────────
os.makedirs("Figure", exist_ok=True)

# ── Chargement des données ─────────────────────────────────────────────────────
df = pd.read_csv("Book1.csv")

# ── Récupération des colonnes ──────────────────────────────────────────────────
# Colonne de la distance diminuée (valeur lue sur le dispositif expérimental)
distance_diminue = df["Distance_diminué"].to_numpy()

# Trois essais de capacité C1 mesurée seule
C1_essai1 = df["C1  pF"].to_numpy()
C1_essai2 = df["C1 (2)"].to_numpy()
C1_essai3 = df["C1(3)"].to_numpy()

# Trois essais de capacité C2 mesurée en présence de C1
C2_essai1 = df["C2 avec C1 pF"].to_numpy()
C2_essai2 = df["C2 avce C1 (2)"].to_numpy()
C2_essai3 = df["C2 avce C1 (3)"].to_numpy()

# ── Calcul de la distance d ────────────────────────────────────────────────────
# d = 8 - distance_diminuée  (distance réelle entre les armatures, en mm)
# L'incertitude sur distance_diminuée se reporte directement sur d
# car d(8 - x)/dx = -1, donc u(d) = u(distance_diminuée)
incertitude_d_diminue = 1 / 9          # incertitude instrumentale sur la lecture
d = 8 - distance_diminue               # distance effective entre armatures
incertitude_d = incertitude_d_diminue  # même valeur, signe sans importance

# ── Moyennes et incertitudes sur les capacités ─────────────────────────────────
# Moyenne arithmétique sur les 3 essais (estimateur de la vraie valeur)
C1_moy = np.mean([C1_essai1, C1_essai2, C1_essai3], axis=0)
C2_moy = np.mean([C2_essai1, C2_essai2, C2_essai3], axis=0)

# Écart-type expérimental (ddof=1 → estimateur non biaisé sur 3 essais)
C1_std = np.std([C1_essai1, C1_essai2, C1_essai3], axis=0, ddof=1)
C2_std = np.std([C2_essai1, C2_essai2, C2_essai3], axis=0, ddof=1)

# Incertitude instrumentale de l'appareil de mesure (donnée constructeur)
incertitude_C1_instr = 0.001  # pF
incertitude_C2_instr = 0.001  # pF

# Incertitude totale : combinaison quadratique de l'incertitude instrumentale
# et de l'incertitude de type A (dispersion / √n)
n = 3
incertitude_C1 = np.sqrt(incertitude_C1_instr**2 + (C1_std / np.sqrt(n))**2)
incertitude_C2 = np.sqrt(incertitude_C2_instr**2 + (C2_std / np.sqrt(n))**2)

# ── Affichage console des résultats ───────────────────────────────────────────
print("d (mm)      :", d)
print("C1 moyen (pF):", C1_moy)
print("C2 moyen (pF):", C2_moy)

# ── Tracé du graphique avec barres d'erreur ───────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))

ax.errorbar(
    d, C1_moy,
    xerr=incertitude_d, yerr=incertitude_C1,
    fmt='o-', capsize=3, label="C1 moyen (pF)"
)
ax.errorbar(
    d, C2_moy,
    xerr=incertitude_d, yerr=incertitude_C2,
    fmt='s-', capsize=3, label="C2 moyen (pF)"
)

ax.set_xlabel("d = 8 − distance_diminué (mm)")
ax.set_ylabel("Capacité (pF)")
ax.set_title("C1 et C2 (moyennes sur 3 essais) en fonction de d")
ax.legend()
ax.grid(True)

# Sauvegarde dans Figure/ puis affichage
fig.tight_layout()
fig.savefig("Figure/C1_C2_vs_d.png", dpi=150)
print("Figure sauvegardée : Figure/C1_C2_vs_d.png")

plt.show()