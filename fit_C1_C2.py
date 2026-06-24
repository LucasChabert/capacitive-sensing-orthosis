import pandas as pd
import numpy as np
from scipy.optimize import least_squares
import matplotlib.pyplot as plt

# ==========================================================
# Chargement des données
# ==========================================================
d0 = 6.5
df = pd.read_csv("Book1.csv")

distance_diminue = df["Distance_diminué"].to_numpy()
d = 8 - distance_diminue

# --- C1 (cellule supérieure) ---
C1_e1 = df["C1  pF"].to_numpy()
C1_e2 = df["C1 (2)"].to_numpy()
C1_e3 = df["C1(3)"].to_numpy()

# --- C2 (cellule inférieure, mesurée avec C1) ---
C2_e1 = df["C2 avec C1 pF"].to_numpy()
C2_e2 = df["C2 avce C1 (2)"].to_numpy()
C2_e3 = df["C2 avce C1 (3)"].to_numpy()

n = 3
incertitude_d = 1 / 9

C1_moy = np.mean([C1_e1, C1_e2, C1_e3], axis=0)
C1_std = np.std([C1_e1, C1_e2, C1_e3], axis=0, ddof=1)
inc_C1 = np.sqrt(0.001**2 + (C1_std / np.sqrt(n))**2)

C2_moy = np.mean([C2_e1, C2_e2, C2_e3], axis=0)
C2_std = np.std([C2_e1, C2_e2, C2_e3], axis=0, ddof=1)
inc_C2 = np.sqrt(0.001**2 + (C2_std / np.sqrt(n))**2)

milieu = 16

# ==========================================================
# Modèle empirique commun : C = A/(min(d,d0)+B) + bord
# A1 = aller (montée), A2 = retour (descente)
# ==========================================================
def modele(params, dd):
    A1, A2, B, bord = params
    y = np.empty(len(dd))
    y[:milieu] = A1 / (np.minimum(d0, dd[:milieu]) + B) + bord
    y[milieu:] = A2 / (np.minimum(dd[milieu:], d0) + B) + bord
    return y

def cout(params, dd, data):
    return data - modele(params, dd)

def ajuste(C_moy):
    mask = np.isfinite(d) & np.isfinite(C_moy) & (d > 0)
    d_fit = d[mask]
    C_fit = C_moy[mask]
    amp = C_fit.max() - C_fit.min()
    x0 = [amp * np.mean(d_fit), amp * np.mean(d_fit), 0.1, np.min(C_moy)]
    res = least_squares(
        cout, x0,
        bounds=([0, 0, 0, 0], [np.inf, np.inf, np.inf, np.inf]),
        args=(d_fit, C_fit)
    )
    return res.x  # A1, A2, B, bord

p1 = ajuste(C1_moy)
p2 = ajuste(C2_moy)
print("C1 : A1=%.4f A2=%.4f B=%.4f bord=%.4f" % tuple(p1))
print("C2 : A1=%.4f A2=%.4f B=%.4f bord=%.4f" % tuple(p2))

# ==========================================================
# Fonction de tracé : 1 figure, données aller/retour + modèle + encart constantes
# ==========================================================
def trace(nom, C_moy, inc_C, params, couleur_titre, fichier):
    A1, A2, B, bord = params

    d_aller, d_retour = d[:milieu], d[milieu:]
    C_aller, C_retour = C_moy[:milieu], C_moy[milieu:]
    inc_a, inc_r = inc_C[:milieu], inc_C[milieu:]

    fig, ax = plt.subplots(figsize=(9, 5.5))

    ax.errorbar(d_aller, C_aller, xerr=incertitude_d, yerr=inc_a,
                fmt='o', color="steelblue", capsize=3, label="Expérimental aller (montée)")
    ax.errorbar(d_retour, C_retour, xerr=incertitude_d, yerr=inc_r,
                fmt='o', color="tomato", capsize=3, label="Expérimental retour (descente)")

    mod_aller = A1 / (np.minimum(d, d0) + B) + bord
    mod_retour = A2 / (np.minimum(d, d0) + B) + bord
    lab_aller = f"Modèle aller  ($A_1$={A1:.3f}, $B$={B:.3f}, $C_b$={bord:.3f}, $d_0$={d0:.2f})"
    lab_retour = f"Modèle retour ($A_2$={A2:.3f}, $B$={B:.3f}, $C_b$={bord:.3f}, $d_0$={d0:.2f})"
    ax.plot(d, mod_aller, color="steelblue", linewidth=2, label=lab_aller)
    ax.plot(d, mod_retour, color="tomato", linewidth=2, label=lab_retour)

    ax.set_xlabel("d (mm)")
    ax.set_ylabel(f"{nom} (pF)")
    ax.set_title(f"{nom} mesuré vs modèle empirique  $A/(\\min(d,d_0)+B)+C_b$")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(loc="upper right", fontsize=9)

    fig.tight_layout()
    fig.savefig(fichier, dpi=150)
    print("→", fichier)

trace("$C_1$", C1_moy, inc_C1, p1, "steelblue", "C1_fit.png")
trace("$C_2$", C2_moy, inc_C2, p2, "darkorange", "C2_fit.png")
