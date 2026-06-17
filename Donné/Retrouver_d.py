import pandas as pd
import numpy as np
from scipy.optimize import least_squares
import matplotlib.pyplot as plt

# ==========================================================
# Chargement des données
# ==========================================================

df = pd.read_csv("Book1.csv")

d = 8 - df["Distance_diminué"].to_numpy()
C2_essai1 = df["C2 avec C1 pF"].to_numpy()
C2_essai2 = df["C2 avce C1 (2)"].to_numpy()
C2_essai3 = df["C2 avce C1 (3)"].to_numpy()

C1_essai1 = df["C1  pF"].to_numpy()
C1_essai2 = df["C1 (2)"].to_numpy()
C1_essai3 = df["C1(3)"].to_numpy()

C1_moy = np.mean([C1_essai1, C1_essai2, C1_essai3], axis=0)
C1_std = np.std([C1_essai1, C1_essai2, C1_essai3], axis=0, ddof=1)
C2_moy = np.mean([C2_essai1, C2_essai2, C2_essai3], axis=0)
C2_stq = np.std([C2_essai1, C2_essai2, C2_essai3], axis=0, ddof=1)

C1_bord = min(np.min(C1_essai1),np.min(C1_essai2),np.min(C1_essai3))
C2_bord = min(np.min(C2_essai1),np.min(C2_essai2),np.min(C2_essai3))

deltad = 8
eS = deltad / (1/np.mean(C2_moy-C2_bord) - 1/np.mean(C1_moy-C1_bord))
d_calc = eS / (C1_moy-C1_bord)


fig1, ax1 = plt.subplots(figsize=(6, 6))
ax1.scatter(d, d_calc, color="steelblue",
            edgecolors="white", linewidths=0.5, s=60)

xmin = min(d.min(), d_calc.min())
xmax = max(d.max(), d_calc.max())
ax1.plot([xmin, xmax], [xmin, xmax], "--", color="gray", label="y = x")

ax1.set_aspect("equal")
ax1.set_xlabel("d calculé")
ax1.set_ylabel("d (pF)")
ax1.set_title("Diagramme de parité")
ax1.grid(True, linestyle="--", alpha=0.4)
ax1.legend()
fig1.tight_layout()
fig1.savefig("d test.png", dpi=150)
plt.show()