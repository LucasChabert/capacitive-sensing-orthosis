"""
mesure_capacites_inverse_et_rapport.py
----------------------------------------
Analyse des capacités C1 et C2 sous forme inverse (1/C) et calcul
d'un rapport normalisé permettant d'estimer la distance d à partir
des mesures de capacité.
Produit trois figures :
  - Figure/C1_inverse_vs_d.png      → 1/C1 en fonction de d
  - Figure/C2_inverse_vs_d.png      → 1/C2 en fonction de d
  - Figure/distance_calculee_vs_d.png → d reconstruit vs d mesuré
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ── Création du dossier de sortie ─────────────────────────────────────────────
os.makedirs("Figure", exist_ok=True)

# ── Chargement des données ─────────────────────────────────────────────────────
df = pd.read_csv("Book1.csv")

# ── Récupération des colonnes ──────────────────────────────────────────────────
distance_diminue = df["Distance_diminué"].to_numpy()

# Trois essais de C1 (condensateur seul)
C1_essai1 = df["C1  pF"].to_numpy()
C1_essai2 = df["C1 (2)"].to_numpy()
C1_essai3 = df["C1(3)"].to_numpy()

# Trois essais de C2 (mesurée en présence de C1)
C2_essai1 = df["C2 avec C1 pF"].to_numpy()
C2_essai2 = df["C2 avce C1 (2)"].to_numpy()
C2_essai3 = df["C2 avce C1 (3)"].to_numpy()

# ── Calcul de la distance d ────────────────────────────────────────────────────
incertitude_d_diminue = 1 / 9   # incertitude instrumentale sur la lecture
d = 8 - distance_diminue        # distance effective entre armatures (mm)
incertitude_d = incertitude_d_diminue  # u(d) = u(distance_diminuée) car |d/dx(8-x)| = 1

# ── Moyennes et incertitudes ───────────────────────────────────────────────────
C1_moy = np.mean([C1_essai1, C1_essai2, C1_essai3], axis=0)
C2_moy = np.mean([C2_essai1, C2_essai2, C2_essai3], axis=0)

# Écart-type expérimental (ddof=1 → estimateur non biaisé sur n=3)
C1_std = np.std([C1_essai1, C1_essai2, C1_essai3], axis=0, ddof=1)
C2_std = np.std([C2_essai1, C2_essai2, C2_essai3], axis=0, ddof=1)

# Incertitudes instrumentales (données constructeur)
incertitude_C1_instr = 0.001  # pF
incertitude_C2_instr = 0.001  # pF

# Incertitude totale : combinaison quadratique type B (instr.) + type A (dispersion/√n)
n = 3
incertitude_C1 = np.sqrt(incertitude_C1_instr**2 + (C1_std / np.sqrt(n))**2)
incertitude_C2 = np.sqrt(incertitude_C2_instr**2 + (C2_std / np.sqrt(n))**2)

# ── Rapport normalisé ──────────────────────────────────────────────────────────
# r = (C1 - C1_ref) / (C2 - C2_ref) où la référence est la première mesure
# Utilisé ensuite pour reconstruire d à partir des capacités
r = (C1_moy - C1_moy[0]) / (C2_moy - C2_moy[0])

# ── Affichage console ──────────────────────────────────────────────────────────
print("d (mm)        :", d)
print("C1 moyen (pF) :", C1_moy)
print("C2 moyen (pF) :", C2_moy)

# ── Figure 1 : 1/C1 en fonction de d ──────────────────────────────────────────
# Pour un condensateur plan idéal : C = ε₀S/d  →  1/C ∝ d (linéaire)
fig1, ax1 = plt.subplots(figsize=(8, 5))
ax1.errorbar(d, 1 / C1_moy,
             xerr=incertitude_d, yerr=incertitude_C1,
             fmt='o-', capsize=3, label="1/C1 (pF⁻¹)")
ax1.set_xlabel("d = 8 − distance_diminué (mm)")
ax1.set_ylabel("1/C1 (pF⁻¹)")
ax1.set_title("Inverse de C1 en fonction de d")
ax1.legend()
ax1.grid(True)
fig1.tight_layout()
fig1.savefig("Figure/C1_inverse_vs_d.png", dpi=150)
print("Figure sauvegardée : Figure/C1_inverse_vs_d.png")

# ── Figure 2 : 1/C2 en fonction de d ──────────────────────────────────────────
fig2, ax2 = plt.subplots(figsize=(9, 5))
ax2.errorbar(d, 1 / C2_moy,
             xerr=incertitude_d, yerr=incertitude_C2,
             fmt='s-', capsize=3, label="1/C2 (pF⁻¹)")
ax2.set_xlabel("d (mm)")
ax2.set_ylabel("1/C2 (pF⁻¹)")
ax2.set_title("Inverse de C2 en fonction de d")
ax2.legend()
ax2.grid(True)
fig2.tight_layout()
fig2.savefig("Figure/C2_inverse_vs_d.png", dpi=150)
print("Figure sauvegardée : Figure/C2_inverse_vs_d.png")

# ── Figure 3 : distance reconstruite vs d mesuré ──────────────────────────────
# Paramètres de référence (point initial de la mesure)
d0     = 6    # distance de référence initiale (mm)
deltad = 10   # plage de variation de d (mm)

# Terme de correction lié au rapport des capacités à l'origine
# Formule : r_eps = (d0 / Δd) × (C1_ref / C2 - 1)
r_eps = d0 / deltad * (C1_moy[0] / C2_moy - 1)

# Distance reconstruite directement depuis le rapport C1/C2 :
# d_reconstruit = 1 / (C1/C2 - 1)
d_from_ratio = 1 / ((C1_moy / C2_moy) - 1)

# Distance reconstruite via le rapport des variations (normalisé par r_eps et Δd) :
# d_calc = (r_eps × Δd) / (ΔC1/ΔC2 - 1)
d_calculated = (r_eps * deltad) / ((C1_moy - C1_moy[0]) / (C2_moy - C2_moy[0]) - 1)

fig3, ax3 = plt.subplots(figsize=(9, 5))
ax3.errorbar(d, d_from_ratio,
             xerr=incertitude_d, yerr=incertitude_C2,
             fmt='s-', capsize=3, label="d reconstruit via C1/C2")
ax3.errorbar(d, d_calculated,
             xerr=incertitude_d, yerr=incertitude_C2,
             fmt='o-', capsize=3, label="d calculé via ΔC1/ΔC2")
ax3.set_xlabel("d mesuré (mm)")
ax3.set_ylabel("d reconstruit (mm)")
ax3.set_title("Distance reconstruite depuis les capacités vs d mesuré")
ax3.legend()
ax3.grid(True)
fig3.tight_layout()
fig3.savefig("Figure/distance_calculee_vs_d.png", dpi=150)
print("Figure sauvegardée : Figure/distance_calculee_vs_d.png")

plt.show()