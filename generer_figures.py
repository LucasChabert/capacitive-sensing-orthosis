"""
generer_figures.py — Régénère les figures du rapport à partir de Book1.csv.
Usage : placer Book1.csv dans le même dossier (ou ajuster le chemin) puis exécuter.
Produit : fig_C_vs_d.pdf, fig_C1_fit.pdf, fig_reconstruction.pdf
"""
import pandas as pd, numpy as np
from scipy.optimize import least_squares
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"font.size": 11, "axes.grid": True, "grid.linestyle": "--",
                     "grid.alpha": 0.4, "figure.dpi": 150, "savefig.bbox": "tight"})

CHEMIN_CSV = "Book1.csv"
df = pd.read_csv(CHEMIN_CSV)
distance_diminue = df["Distance_diminué"].to_numpy()
d = 8 - distance_diminue

C1_essais = np.vstack([df["C1  pF"], df["C1 (2)"], df["C1(3)"]]).astype(float)
C2_essais = np.vstack([df["C2 avec C1 pF"], df["C2 avce C1 (2)"],
                       df["C2 avce C1 (3)"]]).astype(float)

n = 3
t95 = stats.t.ppf(0.975, n - 1)               # facteur de Student, 2 ddl
C1 = C1_essais.mean(0)
C2 = C2_essais.mean(0)
incertitude_C1 = np.sqrt((C1_essais.std(0, ddof=1) / np.sqrt(n))**2 + (0.001 / np.sqrt(3))**2)
incertitude_C2 = np.sqrt((C2_essais.std(0, ddof=1) / np.sqrt(n))**2 + (0.001 / np.sqrt(3))**2)
U1 = t95 * incertitude_C1
U2 = t95 * incertitude_C2
incertitude_d = 1 / 9

milieu = 16
charge = slice(0, milieu)
decharge = slice(milieu, None)

# --- Figure 1 : capacités en fonction de d, branches charge/décharge ---
fig, ax = plt.subplots(figsize=(7.2, 4.6))
ax.errorbar(d[charge], C1[charge], xerr=incertitude_d, yerr=U1[charge], fmt='o-',
            color="#2c6fbb", capsize=2, lw=1, ms=4, label=r"$C_1$ — charge")
ax.errorbar(d[decharge], C1[decharge], xerr=incertitude_d, yerr=U1[decharge], fmt='s--',
            color="#2c6fbb", alpha=.55, capsize=2, lw=1, ms=4, label=r"$C_1$ — décharge")
ax.errorbar(d[charge], C2[charge], xerr=incertitude_d, yerr=U2[charge], fmt='o-',
            color="#e07a1f", capsize=2, lw=1, ms=4, label=r"$C_2$ — charge")
ax.errorbar(d[decharge], C2[decharge], xerr=incertitude_d, yerr=U2[decharge], fmt='s--',
            color="#e07a1f", alpha=.55, capsize=2, lw=1, ms=4, label=r"$C_2$ — décharge")
ax.set_xlabel("$d$ (mm)"); ax.set_ylabel("Capacité (pF)")
ax.set_title("Capacités mesurées en fonction de l'écartement (barres : $U_{95}$)")
ax.legend(fontsize=8.5, ncol=2)
fig.savefig("fig_C_vs_d.pdf"); plt.close(fig)

# --- Figure 2 : ajustement empirique C1 = A/(d+B)+C par branche ---
def ajuste_branche(d_branche, C_branche):
    residu = lambda p: p[0] / (d_branche + p[1]) + p[2] - C_branche
    sol = least_squares(residu, [3, 1, 1],
                        bounds=([0, -3, -3], [60, 12, C_branche.min() + 0.05]))
    return sol.x

p_charge = ajuste_branche(d[charge], C1[charge])
p_decharge = ajuste_branche(d[decharge], C1[decharge])
d_lisse = np.linspace(d.min(), d.max(), 200)
fig, ax = plt.subplots(figsize=(7.2, 4.6))
ax.errorbar(d[charge], C1[charge], xerr=incertitude_d, yerr=U1[charge], fmt='o',
            color="#2c6fbb", capsize=2, ms=4, label="Charge (mesure)")
ax.errorbar(d[decharge], C1[decharge], xerr=incertitude_d, yerr=U1[decharge], fmt='o',
            color="#cc3b2e", capsize=2, ms=4, label="Décharge (mesure)")
ax.plot(d_lisse, p_charge[0] / (d_lisse + p_charge[1]) + p_charge[2],
        color="#2c6fbb", lw=1.8, label=r"Modèle charge $A/(d+B)+C$")
ax.plot(d_lisse, p_decharge[0] / (d_lisse + p_decharge[1]) + p_decharge[2],
        color="#cc3b2e", lw=1.8, label="Modèle décharge")
ax.set_xlabel("$d$ (mm)"); ax.set_ylabel("$C_1$ (pF)")
ax.set_title(r"$C_1$ : ajustement empirique $A/(d+B)+C$ par branche")
ax.legend(fontsize=8.5)
fig.savefig("fig_C1_fit.pdf"); plt.close(fig)

# --- Figure 3 : reconstruction monocellule vs ratiométrique ---
def rmse(a, b): return float(np.sqrt(np.mean((a - b)**2)))

residu_mono = lambda p: p[0] / (C1 - p[2]) - p[1] - d
sol_mono = least_squares(residu_mono, [3, 1, 1],
                         bounds=([0, -5, -5], [60, 12, C1.min() - 1e-3]))
A, B, C = sol_mono.x
d_mono = A / (C1 - C) - B

alpha = d[0] * (C1[0] / C2[0])
d_ratio = alpha * (C2 / C1)

fig, ax = plt.subplots(figsize=(5.6, 5.4))
ax.scatter(d, d_mono, c="#2c6fbb", ec="white", lw=.5, s=42, zorder=4,
           label=f"Monocellule $A/(C_1-C)-B$  (RMSE = {rmse(d_mono, d):.2f} mm)")
ax.scatter(d, d_ratio, c="#cc3b2e", ec="white", lw=.5, s=42, marker="^", zorder=3,
           label=f"Rapport $C_1/C_2$  (RMSE = {rmse(d_ratio, d):.2f} mm)")
lim = [-0.3, 8.6]
ax.plot(lim, lim, "--", c="gray", lw=1.2, label="$y=x$ (idéal)")
ax.set_xlim(lim); ax.set_ylim(lim); ax.set_aspect("equal")
ax.set_xlabel("$d$ imposé (mm)"); ax.set_ylabel("$d$ reconstruit (mm)")
ax.set_title("Qualité de reconstruction de l'écartement")
ax.legend(fontsize=8, loc="upper left")
fig.savefig("fig_reconstruction.pdf"); plt.close(fig)

print("Figures régénérées.")
