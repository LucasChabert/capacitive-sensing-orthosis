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

d = 8 - distance_diminue

# ==========================================================
# Moyennes et incertitudes
# ==========================================================

C1_moy = np.mean(
    [C1_essai1, C1_essai2, C1_essai3],
    axis=0
)

C1_std = np.std(
    [C1_essai1, C1_essai2, C1_essai3],
    axis=0,
    ddof=1
)

C1_bord = np.min(C1_moy)
n = 3

incertitude_d = 1 / 9

incertitude_C1 = np.sqrt(
    0.001**2 +
    (C1_std / np.sqrt(n))**2
)

# ==========================================================
# Modèle avec effet de bord
# ==========================================================

def C1_model_avec_bord(params, d):

    A1, A2, B = params

    N = len(d)
    milieu = 16

    y = np.empty(N)

    # Aller
    y[:milieu] = A1 /(np.minimum(d0,d[:milieu] )+ B) + C1_bord

    # Retour
    y[milieu:] = A2 / (np.minimum(d[milieu:], d0) + B) + C1_bord

    return y


def cout_avec_bord(params, d, C1_data):

    return C1_data - C1_model_avec_bord(params, d)


# ==========================================================
# Préparation des données
# ==========================================================

mask = (
    np.isfinite(d)
    & np.isfinite(C1_moy)
    & (d > 0)
)

d_fit = d[mask]
C1_fit_data = C1_moy[mask]

# ==========================================================
# Ajustement
# ==========================================================

amplitude = C1_fit_data.max() - C1_fit_data.min()

x0 = [
    amplitude * np.mean(d_fit),  # A1
    amplitude * np.mean(d_fit),  # A2
    0.1,                         # B
]

res = least_squares(
    cout_avec_bord,
    x0,
    bounds=(
        [0, 0, 0],
        [np.inf, np.inf, np.inf]
    ),
    args=(d_fit, C1_fit_data)
)

A1, A2, B = res.x



# ==========================================================
# Prédictions et résidus
# ==========================================================

C1_modele = C1_model_avec_bord(res.x, d_fit)

residus = C1_fit_data - C1_modele

# ==========================================================
# Figure 1 : Parité
# ==========================================================

fig1, ax1 = plt.subplots(figsize=(6, 6))

ax1.scatter(
    C1_modele,
    C1_fit_data,
    color="steelblue",
    edgecolors="white",
    linewidths=0.5,
    s=60
)

xmin = min(C1_modele.min(), C1_fit_data.min())
xmax = max(C1_modele.max(), C1_fit_data.max())

ax1.plot(
    [xmin, xmax],
    [xmin, xmax],
    "--",
    color="gray",
    label="y = x"
)

ax1.set_aspect("equal")

ax1.set_xlabel("C1 modèle (pF)")
ax1.set_ylabel("C1 mesuré (pF)")
ax1.set_title("Diagramme de parité")

ax1.grid(True, linestyle="--", alpha=0.4)

ax1.legend()

fig1.tight_layout()

fig1.savefig("../figures/analysis/C1_parity_hysteresis.png",
    dpi=150
)

# ==========================================================
# Figure 2 : Expérimental vs modèle
# ==========================================================

N = len(d)

milieu =16

d_aller = d[:milieu]
d_retour = d[milieu:]

C1_aller = C1_moy[:milieu]
C1_retour = C1_moy[milieu:]

inc_aller = incertitude_C1[:milieu]
inc_retour = incertitude_C1[milieu:]

fig2, ax2 = plt.subplots(figsize=(9, 5))

# Données aller
ax2.errorbar(
    d_aller,
    C1_aller,
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
    C1_retour,
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



C1_modele_aller  = A1 / (np.minimum(d, d0) + B) + C1_bord  
C1_modele_retour = A2 / (np.minimum(d, d0) + B) + C1_bord

ax2.plot(
    d,
    C1_modele_aller,
    color="steelblue",
    linewidth=2,
    linestyle="-",
    label=f"Modèle aller (A1={A1:.3f})"
)

ax2.plot(
    d,
    C1_modele_retour,
    color="tomato",
    linewidth=2,
    linestyle="-",
    label=f"Modèle retour (A2={A2:.3f})"
)
# Figure 2 - ajoute après les ax2.plot(...)
ax2.set_xlabel("d (mm)")
ax2.set_ylabel("C1 (pF)")
ax2.set_title("C1 mesuré vs modèle")
ax2.grid(True, linestyle="--", alpha=0.4)
ax2.legend()          # ← manquait
fig2.tight_layout()
fig2.savefig("../figures/analysis/C1_fit_hysteresis.png", dpi=150)
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

fig3.savefig("../figures/analysis/C1_residus.png",
    dpi=150
)
print(C1_bord)
plt.show()