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

d = 8 - distance_diminue

# ==========================================================
# Moyennes et incertitudes
# ==========================================================

C2_moy = np.mean(
    [C2_essai1, C2_essai2, C2_essai3],
    axis=0
)

C2_std = np.std(
    [C2_essai1, C2_essai2, C2_essai3],
    axis=0,
    ddof=1
)

n = 3

incertitude_d = 1 / 9

incertitude_C2 = np.sqrt(
    0.001**2 +
    (C2_std / np.sqrt(n))**2
)

# ==========================================================
# Modèle avec effet de bord
# ==========================================================

def C2_model_avec_bord(params, d):

    A1, A2, B, C2_bord = params

    N = len(d)
    milieu = N // 2

    y = np.empty(N)

    # Aller
    y[:milieu] = A1 / (d[:milieu] + B) + C2_bord

    # Retour
    y[milieu:] = A2 / (d[milieu:] + B) + C2_bord

    return y


def cout_avec_bord(params, d, C2_data):

    return C2_data - C2_model_avec_bord(params, d)


# ==========================================================
# Préparation des données
# ==========================================================

mask = (
    np.isfinite(d)
    & np.isfinite(C2_moy)
    & (d > 0)
)

d_fit = d[mask]
C2_fit_data = C2_moy[mask]

# ==========================================================
# Ajustement
# ==========================================================

amplitude = C2_fit_data.max() - C2_fit_data.min()

x0 = [
    amplitude * np.mean(d_fit),  # A1
    amplitude * np.mean(d_fit),  # A2
    0.1,                         # B
    C2_fit_data.min()            # Cbord
]

res = least_squares(
    cout_avec_bord,
    x0,
    bounds=(
        [0, 0, 0, -np.inf],
        [np.inf, np.inf, np.inf, np.inf]
    ),
    args=(d_fit, C2_fit_data)
)

A1, A2, B, C2_bord = res.x

print("\n===== PARAMÈTRES AJUSTÉS =====")
print(f"A1       = {A1:.6f}")
print(f"A2       = {A2:.6f}")
print(f"B        = {B:.6f}")
print(f"C2_bord  = {C2_bord:.6f} pF")

# ==========================================================
# Prédictions et résidus
# ==========================================================

C2_modele = C2_model_avec_bord(res.x, d_fit)

residus = C2_fit_data - C2_modele

# ==========================================================
# Figure 1 : Parité
# ==========================================================

fig1, ax1 = plt.subplots(figsize=(6, 6))

ax1.scatter(
    C2_modele,
    C2_fit_data,
    color="steelblue",
    edgecolors="white",
    linewidths=0.5,
    s=60
)

xmin = min(C2_modele.min(), C2_fit_data.min())
xmax = max(C2_modele.max(), C2_fit_data.max())

ax1.plot(
    [xmin, xmax],
    [xmin, xmax],
    "--",
    color="gray",
    label="y = x"
)

ax1.set_aspect("equal")

ax1.set_xlabel("C2 modèle (pF)")
ax1.set_ylabel("C2 mesuré (pF)")
ax1.set_title("Diagramme de parité")

ax1.grid(True, linestyle="--", alpha=0.4)

ax1.legend()

fig1.tight_layout()

fig1.savefig(
    "C2_parity_hysteresis.png",
    dpi=150
)

# ==========================================================
# Figure 2 : Expérimental vs modèle
# ==========================================================

N = len(d)

milieu = N // 2

d_aller = d[:milieu]
d_retour = d[milieu:]

C2_aller = C2_moy[:milieu]
C2_retour = C2_moy[milieu:]

inc_aller = incertitude_C2[:milieu]
inc_retour = incertitude_C2[milieu:]

fig2, ax2 = plt.subplots(figsize=(9, 5))

# Données aller
ax2.errorbar(
    d_aller,
    C2_aller,
    xerr=incertitude_d,
    yerr=inc_aller,
    fmt='o',
    color="steelblue",
    capsize=3,
    label="Expérimental aller"
)

# Données retour
ax2.errorbar(
    d_retour,
    C2_retour,
    xerr=incertitude_d,
    yerr=inc_retour,
    fmt='o',
    color="tomato",
    capsize=3,
    label="Expérimental retour"
)

# ==========================================
# Courbes théoriques lisses
# ==========================================




C2_modele_aller = A1 / (d_modele + B) + C2_bord
C2_modele_retour = A2 / (d_modele + B) + C2_bord

ax2.plot(
    d_modele,
    C2_modele_aller,
    color="steelblue",
    linewidth=2,
    linestyle="-",
    label=f"Modèle aller (A1={A1:.3f})"
)

ax2.plot(
    d_modele,
    C2_modele_retour,
    color="tomato",
    linewidth=2,
    linestyle="-",
    label=f"Modèle retour (A2={A2:.3f})"
)

# ==========================================================
# Figure 3 : Résidus
# ==========================================================

fig3, ax3 = plt.subplots(figsize=(9, 5))

ax3.scatter(
    d_fit,
    residus,
    color="purple",
    edgecolors="white",
    linewidths=0.5,
    s=60
)

ax3.axhline(
    0,
    color="gray",
    linestyle="--"
)

ax3.set_xlabel("d (mm)")
ax3.set_ylabel("Résidu (pF)")

ax3.set_title(
    "Résidus du modèle"
)

ax3.grid(
    True,
    linestyle="--",
    alpha=0.4
)

fig3.tight_layout()

fig3.savefig(
    "C2_residus.png",
    dpi=150
)

plt.show()