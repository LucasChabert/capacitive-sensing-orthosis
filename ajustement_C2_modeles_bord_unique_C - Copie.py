import pandas as pd
import numpy as np
from scipy.optimize import least_squares
import matplotlib.pyplot as plt

# ==========================================================
# Chargement des données
# ==========================================================

df = pd.read_csv("Book1.csv")

distance_diminue = df["Distance_diminué"].to_numpy()
C2_essai1 = df["C2 avec C1 pF"].to_numpy()
C2_essai2 = df["C2 avce C1 (2)"].to_numpy()
C2_essai3 = df["C2 avce C1 (3)"].to_numpy()

C1_essai1 = df["C1  pF"].to_numpy()
C1_essai2 = df["C1 (2)"].to_numpy()
C1_essai3 = df["C1(3)"].to_numpy()

C1_moy = np.mean([C1_essai1, C1_essai2, C1_essai3], axis=0)
C1_std = np.std([C1_essai1, C1_essai2, C1_essai3], axis=0, ddof=1)

d = 8 - distance_diminue

# ==========================================================
# Moyennes et incertitudes
# ==========================================================

C2_moy = np.mean([C2_essai1, C2_essai2, C2_essai3], axis=0)
C2_std = np.std([C2_essai1, C2_essai2, C2_essai3], axis=0, ddof=1)
n = 3

incertitude_d  = 1 / 9
incertitude_C2 = np.sqrt(0.001**2 + (C2_std / np.sqrt(n))**2)

# ==========================================================
# Préparation des données (masque + séparation aller/retour)
# ==========================================================

mask = np.isfinite(d) & np.isfinite(C2_moy) & (d > 0)

d_fit   = d[mask]
C2_fit  = C2_moy[mask]
inc_fit = incertitude_C2[mask]
C1_fit  = C1_moy[mask]

milieu = 16

d_aller    = d_fit[:milieu]
d_retour   = d_fit[milieu:]
C2_aller   = C2_fit[:milieu]
C2_retour  = C2_fit[milieu:]
inc_aller  = inc_fit[:milieu]
inc_retour = inc_fit[milieu:]
C1_aller   = C1_fit[:milieu]
C1_retour  = C1_fit[milieu:]

# ==========================================================
# Constantes physiques
# ==========================================================

S         = 10 * 22
e1_aller  = 5.128918 / (10 * 22)
e1_retour = 7.769379 / (10 * 22)
deltad    = 8
e         = 2
C1_bord = 0.3068042506772991

# ==========================================================
# Modèle : A1/A2 libres, B et C_bord partagés
# ==========================================================

def modele(A, B, C_bord, e1, d, C1):
    C_serie = 1.0 / (1.0/C1  + deltad/(A*S))
    return C_serie + C_bord

def cout_global(params, d_a, d_r, C2_a, C2_r):
    A1, A2, B, C_bord = params
    res_aller  = C2_a - modele(A1, B, C_bord, e1_aller,  d_a, C1_aller)
    res_retour = C2_r - modele(A2, B, C_bord, e1_retour, d_r, C1_retour)
    return np.concatenate([res_aller, res_retour])

# ==========================================================
# Ajustement
# ==========================================================

x0 = [deltad, deltad, e, float(C2_fit.min())]

res = least_squares(
    cout_global,
    x0,
    bounds=([0, 0, 0, -np.inf], [np.inf, np.inf, np.inf, np.inf]),
    args=(d_aller, d_retour, C2_aller, C2_retour)
)

A1, A2, B, C_bord = res.x

print("\n===== PARAMÈTRES AJUSTÉS =====")
print(f"A1      = {A1:.6f}")
print(f"A2      = {A2:.6f}")
print(f"B       = {B:.6f} mm")
print(f"C_bord  = {C_bord:.6f} pF")

# ==========================================================
# Résidus
# ==========================================================

res_vect = cout_global(res.x, d_aller, d_retour, C2_aller, C2_retour)
n_aller  = len(d_aller)
residu_a = res_vect[:n_aller]
residu_r = res_vect[n_aller:]

# ==========================================================
# Figure 1 : Parité
# ==========================================================

C2_mod_aller  = modele(A1, B, C_bord, e1_aller,  d_aller,  C1_aller)
C2_mod_retour = modele(A2, B, C_bord, e1_retour, d_retour, C1_retour)
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
ax1.set_title("Diagramme de parité")
ax1.grid(True, linestyle="--", alpha=0.4)
ax1.legend()
fig1.tight_layout()
fig1.savefig("C2_parity.png", dpi=150)

# ==========================================================
# Figure 2 : Expérimental vs modèle
# ==========================================================

fig2, ax2 = plt.subplots(figsize=(9, 5))

ax2.errorbar(d_aller,  C2_aller,  xerr=incertitude_d, yerr=inc_aller,
             fmt='o', color="steelblue", capsize=3, label="Expérimental aller")
ax2.errorbar(d_retour, C2_retour, xerr=incertitude_d, yerr=inc_retour,
             fmt='o', color="tomato",    capsize=3, label="Expérimental retour")

ax2.plot(d_aller,  modele(A1, B, C_bord, e1_aller,  d_aller,  C1_aller),
         color="steelblue", linewidth=2, label=f"Modèle aller  (A1={A1:.4f})")
ax2.plot(d_retour, modele(A2, B, C_bord, e1_retour, d_retour, C1_retour),
         color="tomato",    linewidth=2, label=f"Modèle retour (A2={A2:.4f})")

ax2.set_xlabel("d (mm)")
ax2.set_ylabel("C2 (pF)")
ax2.set_title("C2 expérimental vs modèle")
ax2.legend()
ax2.grid(True, linestyle="--", alpha=0.4)
fig2.tight_layout()
fig2.savefig("C2_exp_vs_modele.png", dpi=150)

# ==========================================================
# Figure 3 : Résidus
# ==========================================================

fig3, ax3 = plt.subplots(figsize=(9, 5))
ax3.scatter(d_aller,  residu_a, color="steelblue", s=60,
            edgecolors="white", linewidths=0.5, label="Aller")
ax3.scatter(d_retour, residu_r, color="tomato",    s=60,
            edgecolors="white", linewidths=0.5, label="Retour")
ax3.axhline(0, color="gray", linestyle="--")
ax3.set_xlabel("d (mm)")
ax3.set_ylabel("Résidu (pF)")
ax3.set_title("Résidus du modèle")
ax3.legend()
ax3.grid(True, linestyle="--", alpha=0.4)
fig3.tight_layout()
fig3.savefig("C2_residus.png", dpi=150)

plt.show()