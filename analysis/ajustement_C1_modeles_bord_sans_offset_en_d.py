"""
ajustement_C1_modeles_bord.py
------------------------------
Ajustement de la capacité C1 par deux modèles (avec et sans effet de bord)
sur trois segments : montée, descente, et trajet complet.
Produit deux figures :
  - figures/analysis/C1_parity_hysteresis.png  → graphe de parité (modèle vs mesure)
  - figures/analysis/C1_model_vs_exp.png       → données expérimentales + courbes ajustées
"""

import os
import pandas as pd
import numpy as np
from scipy.optimize import least_squares
import matplotlib.pyplot as plt

# ── Création du dossier de sortie ─────────────────────────────────────────────
os.makedirs("../figures/analysis", exist_ok=True)

# ── Chargement des données ─────────────────────────────────────────────────────
df = pd.read_csv("../data/Book1.csv")

distance_diminue = df["Distance_diminué"].to_numpy()

# Trois essais de C1 (condensateur seul)
C1_essai1 = df["C1  pF"].to_numpy()
C1_essai2 = df["C1 (2)"].to_numpy()
C1_essai3 = df["C1(3)"].to_numpy()

# Trois essais de C2 (en présence de C1) — chargés mais non utilisés ici
C2_essai1 = df["C2 avec C1 pF"].to_numpy()
C2_essai2 = df["C2 avce C1 (2)"].to_numpy()
C2_essai3 = df["C2 avce C1 (3)"].to_numpy()

# Distance effective entre armatures
d = 8 - distance_diminue

# ── Moyennes et incertitudes ───────────────────────────────────────────────────
C1_moy = np.mean([C1_essai1, C1_essai2, C1_essai3], axis=0)
C2_moy = np.mean([C2_essai1, C2_essai2, C2_essai3], axis=0)

# Écart-type expérimental (ddof=1 → estimateur non biaisé sur n=3)
C1_std = np.std([C1_essai1, C1_essai2, C1_essai3], axis=0, ddof=1)
C2_std = np.std([C2_essai1, C2_essai2, C2_essai3], axis=0, ddof=1)

n = 3
incertitude_d  = 1 / 9  # incertitude instrumentale sur d (mm)
# Combinaison quadratique : incertitude instrumentale (type B) + dispersion/√n (type A)
incertitude_C1 = np.sqrt(0.001**2 + (C1_std / np.sqrt(n))**2)
incertitude_C2 = np.sqrt(0.001**2 + (C2_std / np.sqrt(n))**2)

# ── Modèles physiques pour C1 ──────────────────────────────────────────────────
# Modèle avec effet de bord : C1 = A/d + C1_bord
# A        : produit ε₀·S (permittivité × surface des armatures)
# C1_bord  : capacité parasite résiduelle (effets de frange)
def C1_model_avec_bord(params, d):
    A, C1_bord = params
    return A / d + C1_bord

# Modèle sans effet de bord : C1 = A/d  (condensateur plan idéal)
def C1_model_sans_bord(params, d):
    A, = params
    return A / d

# Fonctions de coût (résidus) pour least_squares
def cout_avec_bord(params, d, C1_data):
    return C1_data - C1_model_avec_bord(params, d)

def cout_sans_bord(params, d, C1_data):
    return C1_data - C1_model_sans_bord(params, d)

# ── Découpage montée / descente / trajet complet ───────────────────────────────
# Indices 0–15 : phase de montée (d croissant)
# Indices 16–30 : phase de descente (d décroissant)
# "Trajet" : ajustement global sur l'ensemble des points
montee   = df.iloc[0:16].copy()
descente = df.iloc[16:31].copy()

etapes   = {"Montée": montee, "Descente": descente, "Trajet": df}
couleurs = {"Montée": "steelblue", "Descente": "tomato", "Trajet": "darkmagenta"}

# Dictionnaires pour stocker les paramètres ajustés par segment
params_avec_bord = {}
params_sans_bord = {}

# ── Figure 1 : graphe de parité ────────────────────────────────────────────────
# Permet de visualiser si le modèle suit bien les données :
# un bon ajustement aligne tous les points sur la droite y = x.
fig1, ax1 = plt.subplots(figsize=(6, 6))

for nom, df_etape in etapes.items():
    idx   = df_etape.index          # indices dans le DataFrame global
    d_et  = 8 - df_etape["Distance_diminué"].to_numpy()
    C1_et = C1_moy[idx]            # on réutilise la moyenne déjà calculée

    # Filtrage : points physiquement valides (d > 0, pas de NaN)
    mask  = np.isfinite(d_et) & np.isfinite(C1_et) & (d_et > 0)
    d_et  = d_et[mask]
    C1_et = C1_et[mask]

    # Initialisation heuristique : A ≈ amplitude × d moyen, C1_bord ≈ minimum
    x0_avec = [(C1_et.max() - C1_et.min()) * d_et.mean(), C1_et.min()]
    res_avec = least_squares(cout_avec_bord, x0_avec, args=(d_et, C1_et), verbose=0)
    params_avec_bord[nom] = res_avec.x

    x0_sans = [(C1_et.max() - C1_et.min()) * d_et.mean()]
    res_sans = least_squares(cout_sans_bord, x0_sans, args=(d_et, C1_et), verbose=0)
    params_sans_bord[nom] = res_sans.x

    A_avec, C1_bord_opt = res_avec.x
    A_sans,             = res_sans.x

    print(f"\n--- {nom} ---")
    print(f"  Avec bord : A={A_avec:.6f}, C1_bord={C1_bord_opt:.6f} pF")
    print(f"  Sans bord : A={A_sans:.6f}")

    # Valeurs prédites par le modèle avec bord pour le graphe de parité
    C1_predit = C1_model_avec_bord(res_avec.x, d_et)
    ax1.scatter(C1_predit, C1_et,
                color=couleurs[nom], edgecolors="white", linewidths=0.5, s=60, zorder=5,
                label=f"{nom}  (A={A_avec:.3f}, C1b={C1_bord_opt:.3f} pF)")

# Droite y = x : alignement parfait modèle / mesure
lim_vals = [ax1.get_xlim()[0], ax1.get_xlim()[1],
            ax1.get_ylim()[0], ax1.get_ylim()[1]]
lim = (min(lim_vals) - 0.05, max(lim_vals) + 0.05)
ax1.plot(lim, lim, color="gray", linewidth=1.2, linestyle="--", label="y = x (idéal)")
ax1.set_xlim(lim)
ax1.set_ylim(lim)
ax1.set_aspect("equal")
ax1.set_xlabel("C1 modèle (pF)")
ax1.set_ylabel("C1 mesuré (pF)")
ax1.set_title("Parité C1 — montée vs descente")
ax1.legend(fontsize=8)
ax1.grid(True, linestyle="--", alpha=0.4)
fig1.tight_layout()
fig1.savefig("../figures/analysis/C1_parity_hysteresis.png", dpi=150)
print("\nFigure sauvegardée : figures/analysis/C1_parity_hysteresis.png")

# ── Figure 2 : données expérimentales vs courbes ajustées ─────────────────────
# Masques pour isoler montée et descente sur le vecteur global d
mask_all = np.isfinite(d) & (d > 0)

mask_aller      = mask_all.copy()
mask_aller[16:] = False   # indices 0–15 uniquement

mask_retour      = mask_all.copy()
mask_retour[:16] = False  # indices 16–30 uniquement

d_exp_aller   = d[mask_aller]
C1_exp_aller  = C1_moy[mask_aller]
inc_C1_aller  = incertitude_C1[mask_aller]

d_exp_retour  = d[mask_retour]
C1_exp_retour = C1_moy[mask_retour]
inc_C1_retour = incertitude_C1[mask_retour]

# Déballage des paramètres ajustés pour chaque segment
A_aller_avec,  C1_bord_aller  = params_avec_bord["Montée"]
A_retour_avec, C1_bord_retour = params_avec_bord["Descente"]
A_trajet_avec, C1_bord_trajet = params_avec_bord["Trajet"]
A_aller_sans,                 = params_sans_bord["Montée"]
A_retour_sans,                = params_sans_bord["Descente"]
A_trajet_sans,                = params_sans_bord["Trajet"]

fig2, ax2 = plt.subplots(figsize=(9, 5))

# Points expérimentaux avec barres d'erreur
ax2.errorbar(d_exp_aller, C1_exp_aller,
             xerr=incertitude_d, yerr=inc_C1_aller,
             fmt='o-', color="steelblue", capsize=3, linewidth=1,
             label="C1 expérimental — montée")

ax2.errorbar(d_exp_retour, C1_exp_retour,
             xerr=incertitude_d, yerr=inc_C1_retour,
             fmt='o-', color="tomato", capsize=3, linewidth=1,
             label="C1 expérimental — descente")

# Courbes ajustées — modèle avec effet de bord (trait mixte)
ax2.plot(d_exp_aller,  C1_model_avec_bord(params_avec_bord["Montée"],   d_exp_aller),
         color="steelblue", linewidth=1.5, linestyle="-.",
         label=f"Avec bord — montée   (A={A_aller_avec:.3f}, C1b={C1_bord_aller:.3f})")

ax2.plot(d_exp_retour, C1_model_avec_bord(params_avec_bord["Descente"], d_exp_retour),
         color="tomato", linewidth=1.5, linestyle="-.",
         label=f"Avec bord — descente (A={A_retour_avec:.3f}, C1b={C1_bord_retour:.3f})")

ax2.plot(d, C1_model_avec_bord(params_avec_bord["Trajet"], d),
         color="darkmagenta", linewidth=1.5, linestyle="-.",
         label=f"Avec bord — trajet   (A={A_trajet_avec:.3f}, C1b={C1_bord_trajet:.3f})")


ax2.set_xlabel("d (mm)")
ax2.set_ylabel("C1 (pF)")
ax2.set_title("C1 expérimental vs modèles (avec / sans effet de bord)")
ax2.legend(fontsize=8)
ax2.grid(True, linestyle="--", alpha=0.4)
fig2.tight_layout()
fig2.savefig("../figures/analysis/C1_model_vs_exp.png", dpi=150)
print("Figure sauvegardée : figures/analysis/C1_model_vs_exp.png")

plt.show()