"""
Analyse d'un capteur capacitif différentiel.
Implémente :
    alpha = (C1,0/C2,0 - 1) * d0/Delta_d            (eq. eps_ref)
    d     = alpha * Delta_d / (C1/C2 - 1)            (eq. d_final, formule encadrée)

Corrections par rapport au script de départ :
- Le fichier fourni est Book1.xlsx (Excel), pas un .csv -> lecture avec pd.read_excel.
- Les noms de colonnes réels du fichier ont été repris tels quels (espaces compris,
  ex. "C1  pF", "d ").
- La colonne "d " existe déjà dans le fichier (distance vraie de référence) : on
  l'utilise directement au lieu de la recalculer depuis "Distance_diminué".
- Le modèle eS/(C1-C1_bord) du script initial ne correspond pas à la formule encadrée
  du document ; il est remplacé par celle-ci.
"""

import pandas as pd
import numpy as np
from scipy.optimize import least_squares
import matplotlib.pyplot as plt

# ==========================================================
# 1) Chargement et nettoyage des données
# ==========================================================

df = pd.read_excel("Book1.xlsx", sheet_name="Sheet1")
df = df.dropna(subset=["d "]).reset_index(drop=True)  # enlève les lignes vides en bas de feuille

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
C1_bord = 0.3
C2_bord = 0.3
# ==========================================================
# 2) Constantes de calibration
# ==========================================================
# A ADAPTER avec vos VRAIES valeurs de calibration si elles diffèrent !
# Par défaut on prend comme point de référence la première mesure (Tour = 0,
# d = 6) et comme Delta_d l'amplitude totale du balayage. Si votre calibration
# a été faite séparément (autre mesure, autre Delta_d connu mécaniquement),
# remplacez les 4 lignes ci-dessous par vos valeurs réelles.

i_ref = 0  # index de la mesure de référence (Tour = 0)
d0 = d_vrai[i_ref]
C1_0 = C1_moy[i_ref] - C1_bord
C2_0 = C2_moy[i_ref] -  C2_bord
Delta_d = d_vrai.max() - d_vrai.min()  # amplitude totale du balayage mécanique

alpha_calib = (C1_0 / C2_0 - 1) * d0 / Delta_d
print(f"Calibration directe (eq. eps_ref) : alpha = {alpha_calib:.6f}")

# ==========================================================
# 3) Calcul de d 
# ==========================================================

def d_modele(C1, C2, alpha, Delta_d):
    return alpha * Delta_d / ((C1 - C1_bord) /( C2 - C2_bord)- 1)

d_calc_calib = d_modele(C1_moy, C2_moy, alpha_calib, Delta_d) - 1.22

# ==========================================================
# 4) Recalage de alpha par moindres carrés (optionnel, plus robuste)
#    On ajuste alpha pour minimiser l'écart entre d_calc et d_vrai
#    mesuré, ce qui sert de vérification / alternative à la calibration
#    "un point" ci-dessus.
# ==========================================================


# ==========================================================
# 5) Indicateurs d'erreur
# ==========================================================

def rmse(a, b):
    return np.sqrt(np.mean((a - b) ** 2))

print(f"RMSE (alpha calibration directe) : {rmse(d_calc_calib, d_vrai):.4f}")


# ==========================================================
# 6) Diagramme de parité
# ==========================================================

fig, ax = plt.subplots(figsize=(6, 6))
ax.scatter(d_vrai, d_calc_calib, color="steelblue", edgecolors="white",
           linewidths=0.5, s=60, label="alpha calibration directe")


xmin = min(d_vrai.min(), d_calc_calib.min())
xmax = max(d_vrai.max(), d_calc_calib.max())
ax.plot([xmin, xmax], [xmin, xmax], "--", color="gray", label="y = x")

ax.set_aspect("equal")
ax.set_xlabel("d réel (mesure de référence)")
ax.set_ylabel("d calculé ")
ax.set_title("Diagramme de parité")
ax.grid(True, linestyle="--", alpha=0.4)
ax.legend()
fig.tight_layout()
fig.savefig("d_test.png", dpi=150)
plt.show()