import pandas as pd
import numpy as np
from scipy.optimize import least_squares
import matplotlib.pyplot as plt

# ==========================================================
# Chargement des données
# ==========================================================

d0 = 6.5

df = pd.read_csv("../data/Book1.csv")

distance_diminue = df["Distance_diminué"].to_numpy()

C1_essai1 = df["C1  pF"].to_numpy()
C1_essai2 = df["C1 (2)"].to_numpy()
C1_essai3 = df["C1(3)"].to_numpy()

C2_essai1 = df["C2 avec C1 pF"].to_numpy()
C2_essai2 = df["C2 avce C1 (2)"].to_numpy()
C2_essai3 = df["C2 avce C1 (3)"].to_numpy()

d = 8 - distance_diminue

# ==========================================================
# Moyennes et incertitudes C1
# ==========================================================

C1_moy = np.mean([C1_essai1, C1_essai2, C1_essai3], axis=0)
C1_std = np.std( [C1_essai1, C1_essai2, C1_essai3], axis=0, ddof=1)

# ==========================================================
# Moyennes et incertitudes C2
# ==========================================================

C2_moy = np.mean([C2_essai1, C2_essai2, C2_essai3], axis=0)
C2_std = np.std( [C2_essai1, C2_essai2, C2_essai3], axis=0, ddof=1)
n = 3

incertitude_d  = 1 / 9
incertitude_C1 = np.sqrt(0.001**2 + (C1_std / np.sqrt(n))**2)
incertitude_C2 = np.sqrt(0.001**2 + (C2_std / np.sqrt(n))**2)

# ==========================================================
# Masque et séparation aller / retour
# ==========================================================

milieu = 16

mask = np.isfinite(d) & np.isfinite(C1_moy) & np.isfinite(C2_moy) & (d > 0)

d_fit  = d[mask]
C1_fit = C1_moy[mask]
C2_fit = C2_moy[mask]

d_aller    = d_fit[:milieu]
d_retour   = d_fit[milieu:]
C1_aller   = C1_fit[:milieu]
C1_retour  = C1_fit[milieu:]
C2_aller   = C2_fit[:milieu]
C2_retour  = C2_fit[milieu:]

inc_C2_aller  = incertitude_C2[mask][:milieu]
inc_C2_retour = incertitude_C2[mask][milieu:]
C1_bord = np.min(C1_moy)
# ==========================================================
# ÉTAPE 1 : Fit C1  (recopié depuis le script C1)
# ==========================================================

def C1_model(params, d, branche):
    """
    branche = 'aller'  → utilise A1
    branche = 'retour' → utilise A2
    """
    A1, A2, B = params
    A = A1 if branche == 'aller' else A2
    return A / (np.minimum(d, d0) + B) + C1_bord


def cout_C1(params, d_a, d_r, C1_a, C1_r):
    res_a = C1_a - C1_model(params, d_a, 'aller')
    res_r = C1_r - C1_model(params, d_r, 'retour')
    return np.concatenate([res_a, res_r])


amplitude = C1_fit.max() - C1_fit.min()
x0_C1 = [
    amplitude * np.mean(d_fit),   # A1
    amplitude * np.mean(d_fit),   # A2
    0.1,                           # B
]


res_C1 = least_squares(
    cout_C1,
    x0_C1,
    bounds=([0, 0, 0], [np.inf, np.inf, np.inf]),
    args=(d_aller, d_retour, C1_aller, C1_retour)
)

A1_C1, A2_C1, B_C1 = res_C1.x
C1_bord_fit = C1_bord
print("===== PARAMÈTRES FIT C1 =====")
print(f"A1_C1    = {A1_C1:.6f}")
print(f"A2_C1    = {A2_C1:.6f}")
print(f"B_C1     = {B_C1:.6f}")
print(f"C1_bord  = {C1_bord_fit:.6f} pF")

# Tableaux C1 calculés par le modèle (ce qu'on injecte dans C2)
C1_mod_aller  = C1_model((A1_C1, A2_C1, B_C1), d_aller,  'aller')
C1_mod_retour = C1_model((A1_C1, A2_C1, B_C1), d_retour, 'retour')

# ==========================================================
# Constantes physiques C2
# ==========================================================

S         = 10 * 22
e1_aller  = 5.128918  / (10 * 22)
e1_retour = 7.769379  / (10 * 22)
deltad    = 8
e         = 2

# ==========================================================
# ÉTAPE 2 : Fit C2  (utilise C1_modèle, pas C1_mesuré)
# ==========================================================

def modele_C2(A, B, C_bord, d, C1_mod):
    """C2 = C_serie + C_bord, avec C1 issu du modèle C1."""
    C_serie = 1.0 / (1.0 / C1_mod  + A) 
    return C_serie + C_bord


def cout_C2(params, d_a, d_r, C2_a, C2_r):
    A1, A2, B, C_bord = params
    res_a = C2_a - modele_C2(A1, B, C_bord, d_a, C1_mod_aller)
    res_r = C2_r - modele_C2(A2, B, C_bord, d_r, C1_mod_retour)
    return np.concatenate([res_a, res_r])


x0_C2 = [deltad, deltad, e, float(C2_fit.min())]

res_C2 = least_squares(
    cout_C2,
    x0_C2,
    bounds=([0, 0, 0, -np.inf], [np.inf, np.inf, np.inf, np.inf]),
    args=(d_aller, d_retour, C2_aller, C2_retour)
)

A1_C2, A2_C2, B_C2, C_bord_C2 = res_C2.x

print("\n===== PARAMÈTRES FIT C2 =====")
print(f"A1      = {A1_C2:.6f}")
print(f"A2      = {A2_C2:.6f}")
print(f"B       = {B_C2:.6f} mm")
print(f"C_bord  = {C_bord_C2:.6f} pF")

# ==========================================================
# Résidus C2
# ==========================================================

res_vect = cout_C2(res_C2.x, d_aller, d_retour, C2_aller, C2_retour)
n_aller  = len(d_aller)
residu_a = res_vect[:n_aller]
residu_r = res_vect[n_aller:]

# ==========================================================
# Figure 1 : Parité C2
# ==========================================================

C2_mod_aller  = modele_C2(A1_C2, B_C2, C_bord_C2, d_aller,  C1_mod_aller)
C2_mod_retour = modele_C2(A2_C2, B_C2, C_bord_C2, d_retour, C1_mod_retour)
C2_modele_all = np.concatenate([C2_mod_aller, C2_mod_retour])
C2_data_all   = np.concatenate([C2_aller, C2_retour])

fig1, ax1 = plt.subplots(figsize=(6, 6))
ax1.scatter(C2_modele_all, C2_data_all, color="steelblue",
            edgecolors="white", linewidths=0.5, s=60)

xmin = min(C2_modele_all.min(), C2_data_all.min())
xmax = max(C2_modele_all.max(), C2_data_all.max())
ax1.plot([xmin, xmax], [xmin, xmax], "--", color="gray", label="y = x")

ax1.set_aspect("equal")
ax1.set_xlabel("C2 modèle (pF)")
ax1.set_ylabel("C2 mesuré (pF)")
ax1.set_title("Diagramme de parité – C2")
ax1.grid(True, linestyle="--", alpha=0.4)
ax1.legend()
fig1.tight_layout()
fig1.savefig("../figures/analysis/C2_parity.png", dpi=150)

# ==========================================================
# Figure 2 : Expérimental vs modèle C2
# ==========================================================

fig2, ax2 = plt.subplots(figsize=(9, 5))

ax2.errorbar(d_aller,  C2_aller,  xerr=incertitude_d, yerr=inc_C2_aller,
             fmt='o', color="steelblue", capsize=3, label="Expérimental aller")
ax2.errorbar(d_retour, C2_retour, xerr=incertitude_d, yerr=inc_C2_retour,
             fmt='o', color="tomato",    capsize=3, label="Expérimental retour")

ax2.plot(d_aller,  C2_mod_aller,
         color="steelblue", linewidth=2, label=f"Modèle aller  (A1={A1_C2:.4f})")
ax2.plot(d_retour, C2_mod_retour,
         color="tomato",    linewidth=2, label=f"Modèle retour (A2={A2_C2:.4f})")

ax2.set_xlabel("d (mm)")
ax2.set_ylabel("C2 (pF)")
ax2.set_title("C2 expérimental vs modèle")
ax2.legend()
ax2.grid(True, linestyle="--", alpha=0.4)
fig2.tight_layout()
fig2.savefig("../figures/analysis/C2_exp_vs_modele.png", dpi=150)

# ==========================================================
# Figure 3 : Résidus C2
# ==========================================================

fig3, ax3 = plt.subplots(figsize=(9, 5))
ax3.scatter(d_aller,  residu_a, color="steelblue", s=60,
            edgecolors="white", linewidths=0.5, label="Aller")
ax3.scatter(d_retour, residu_r, color="tomato",    s=60,
            edgecolors="white", linewidths=0.5, label="Retour")
ax3.axhline(0, color="gray", linestyle="--")
ax3.set_xlabel("d (mm)")
ax3.set_ylabel("Résidu (pF)")
ax3.set_title("Résidus du modèle C2")
ax3.legend()
ax3.grid(True, linestyle="--", alpha=0.4)
fig3.tight_layout()
fig3.savefig("../figures/analysis/C2_residus.png", dpi=150)

plt.show()