

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==========================================================
# 1) Chargement et nettoyage des données
# ==========================================================

df = pd.read_excel("../data/Book1.xlsx", sheet_name="Sheet1")
df = df.dropna(subset=["d "]).reset_index(drop=True)  # enlève les lignes vides en bas de feuille
df = df[df["d "] >= 0].reset_index(drop=True)  # on rogne les valeurs négatives de d

d_vrai = df["d "].to_numpy()  # distance de référence (déjà calculée dans le fichier)

C1_essai1 = df["C1  pF"].to_numpy()
C1_essai2 = df["C1 (2)"].to_numpy()
C1_essai3 = df["C1(3)"].to_numpy()

C2_essai1 = df["C2 avec C1 pF"].to_numpy()
C2_essai2 = df["C2 avce C1 (2)"].to_numpy()
C2_essai3 = df["C2 avce C1 (3)"].to_numpy()

C1_moy = np.mean([C1_essai1, C1_essai2, C1_essai3], axis=0)
C1_std = np.std([C1_essai1, C1_essai2, C1_essai3], axis=0, ddof=1)
C2_moy = np.mean([C2_essai1, C2_essai2, C2_essai3], axis=0)
C2_std = np.std([C2_essai1, C2_essai2, C2_essai3], axis=0, ddof=1)

C1_bord = 0
C2_bord = 0

# ==========================================================
# 2) Constantes de calibration
# ==========================================================
# A ADAPTER avec vos VRAIES valeurs de calibration si elles diffèrent !

i_ref = 0  # index de la mesure de référence (Tour = 0)
d0 = d_vrai[i_ref]
C1_0 = C1_moy[i_ref] - C1_bord
C2_0 = C2_moy[i_ref] - C2_bord
Delta_d = 8
alpha_calib = (C1_0 / C2_0 - 1) * d0 / Delta_d
print(f"Calibration directe (eq. eps_ref) : alpha = {alpha_calib:.6f}")

# ==========================================================
# 3) Calcul de d
# ==========================================================

def d_modele(C1, C2, alpha, Delta_d):
    return alpha * Delta_d / ((C1 - C1_bord) / (C2 - C2_bord) - 1)

d_calc = d_modele(C1_moy, C2_moy, alpha_calib, Delta_d) - 1.22

# ==========================================================
# 4) Indicateurs d'erreur
# ==========================================================

def rmse(a, b):
    return np.sqrt(np.mean((a - b) ** 2))

print(f"RMSE (alpha calibration directe) : {rmse(d_calc, d_vrai):.4f}")

# ==========================================================
# 5) Découpage aller / retour
# ==========================================================
# Le balayage va de d_max à d_min (aller) puis remonte de d_min à d_max
# (retour). Le point de retournement est l'indice du minimum de d_vrai.

i_min = np.argmin(d_vrai)

aller = slice(0, i_min + 1)        # inclut le point de retournement
retour = slice(i_min + 1, None)    # ne le recompte pas deux fois

d_aller, d_retour = d_vrai[aller], d_vrai[retour]
dc_aller, dc_retour = d_calc[aller], d_calc[retour]

# ==========================================================
# 6) Courbe C(d) : C1 et C2 en fonction de la distance
# ==========================================================
# d_vrai n'est pas monotone (aller puis retour) : on sépare les deux
# tracés pour éviter qu'une ligne ne relie à tort un point de l'aller à un
# point du retour (zigzag artificiel).

C1_aller, C1_retour = C1_moy[aller], C1_moy[retour]
C2_aller, C2_retour = C2_moy[aller], C2_moy[retour]

fig1, ax1 = plt.subplots(figsize=(7, 5))
ax1.plot(d_aller, C1_aller, "o-", color="steelblue", label="C1 (aller)")
ax1.plot(d_retour, C1_retour, "o--", color="steelblue", alpha=0.6, label="C1 (retour)")
ax1.plot(d_aller, C2_aller, "s-", color="darkorange", label="C2 (aller)")
ax1.plot(d_retour, C2_retour, "s--", color="darkorange", alpha=0.6, label="C2 (retour)")
ax1.set_xlabel("d (distance)")
ax1.set_ylabel("Capacité (pF)")
ax1.set_title("Capacités C1 et C2 en fonction de la distance")
ax1.grid(True, linestyle="--", alpha=0.4)
ax1.legend()
fig1.tight_layout()
fig1.savefig("../figures/analysis/C_en_fonction_de_d.png", dpi=150)

# ==========================================================
# 7) Courbe d'erreur relative (erreur / valeur) en fonction de d,
#    séparément pour l'aller et le retour
# ==========================================================
# ATTENTION : d_vrai contient une valeur 0 (division par zéro -> point
# exclu du calcul de l'erreur relative, sinon il "explose" et écrase le
# graphique).

def erreur_relative(d_calc_sub, d_vrai_sub):
    d_vrai_sub = np.asarray(d_vrai_sub, dtype=float)
    err = (d_calc_sub - d_vrai_sub) / d_vrai_sub
    err[d_vrai_sub == 0] = np.nan  # évite la division par zéro
    return err

err_aller = erreur_relative(dc_aller, d_aller)
err_retour = erreur_relative(dc_retour, d_retour)

fig2, ax2 = plt.subplots(figsize=(7, 5))

ax2.plot(d_aller, err_aller, "o-", color="steelblue", label="Aller")
ax2.plot(d_retour, err_retour, "s-", color="darkorange", label="Retour")
ax2.axhline(0, color="gray", linestyle="--", linewidth=1)
ax2.set_xlabel("d (distance)")
ax2.set_ylabel("Erreur relative (d_calc - d_vrai) / d_vrai")
ax2.set_title("Erreur relative en fonction de la distance — aller / retour")
ax2.grid(True, linestyle="--", alpha=0.4)
ax2.legend()
fig2.tight_layout()
fig2.savefig("../figures/analysis/erreur_relative_aller_retour.png", dpi=150)


fig3, ax3 = plt.subplots(figsize=(6, 6))

ax3.scatter(
    d_calc,
    d_vrai,
    color="steelblue",
    edgecolors="white",
    linewidths=0.5,
    s=60
)

xmin = min(d_calc.min(), d_calc.min())
xmax = max(d_vrai.max(), d_vrai.max())
ax3.plot(xmin, xmax, color="gray", linewidth=1.2, linestyle="--", label="y = x (idéal)")

ax3.plot(
    [xmin, xmax],
    [xmin, xmax],
    "--",
    color="gray",
    label="y = x"
)

ax3.set_aspect("equal")

ax3.set_xlabel("C1 modèle (pF)")
ax3.set_ylabel("C1 mesuré (pF)")
ax3.set_title("Diagramme de parité")

ax3.grid(True, linestyle="--", alpha=0.4)

ax3.legend()

fig3.tight_layout()

fig3.savefig("../figures/analysis/C1_parity_hysteresis.png",
    dpi=150
)


plt.show()
