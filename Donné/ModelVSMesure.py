import pandas as pd
import numpy as np
from scipy.optimize import least_squares
import matplotlib.pyplot as plt

df = pd.read_csv("Book1.csv")

# --- Découpage montée / descente ---
montee   = df.iloc[0:16].copy()
descente = df.iloc[16:31].copy()

etapes = {
    "Montée"  : montee,
    "Descente": descente,
}

couleurs = {
    "Montée"  : "steelblue",
    "Descente": "tomato",
}

C1_essai1 = df["C1  pF"].to_numpy()
C1_essai2 = df["C1 (2)"].to_numpy()
C1_essai3 = df["C1(3)"].to_numpy()
C1_moy = np.mean([C1_essai1, C1_essai2, C1_essai3], axis=0)

def C1_model(params, d):
    A, C1_bord = params
    return A / d + C1_bord


def cout(params, d, C1_data):
    return C1_data - C1_model(params, d)


fig, ax = plt.subplots(figsize=(6, 6))

for nom, df_etape in etapes.items():
    d  = 8 - df_etape["Distance_diminué"].to_numpy()
    C1 = df_etape["C1  pF"].to_numpy()

    mask = np.isfinite(d) & np.isfinite(C1) & (d > 0)
    d    = d[mask]
    C1   = C1[mask]

    A_init       = (C1.max() - C1.min()) * d.mean()
    C1_bord_init = C1.min()
    x0           = [A_init, C1_bord_init]

    res = least_squares(cout, x0, args=(d, C1), verbose=0)
    A_opt, C1_bord_opt = res.x

    print(f"\n--- {nom} ---")
    print(f"  A (=e*S)  = {A_opt:.6f}")
    print(f"  C1_bord   = {C1_bord_opt:.6f} pF")

    C1_predit = C1_model(res.x, d)

    ax.scatter(C1_predit, C1, color=couleurs[nom], edgecolors="white",
               linewidths=0.5, s=60, zorder=5,
               label=f"{nom}  (A={A_opt:.3f}, C1b={C1_bord_opt:.3f} pF)")

# Droite idéale
all_vals = ax.get_xlim() + ax.get_ylim()
lim = (min(all_vals) - 0.05, max(all_vals) + 0.05)
ax.plot(lim, lim, color="gray", linewidth=1.2, linestyle="--", label="y = x (idéal)")

ax.set_xlim(lim)
ax.set_ylim(lim)
ax.set_aspect("equal")
ax.set_xlabel("C1 modèle (pF)")
ax.set_ylabel("C1 mesuré (pF)")
ax.set_title("Parité C1 — montée vs descente")
ax.legend(fontsize=8)
ax.grid(True, linestyle="--", alpha=0.4)

plt.tight_layout()
plt.show()