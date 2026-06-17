import pandas as pd
import numpy as np
from scipy.optimize import least_squares
import matplotlib.pyplot as plt

# --- Chargement ---
df = pd.read_csv("Book1.csv")

distance_diminue = df["Distance_diminué"].to_numpy()

C1_essai1 = df["C1  pF"].to_numpy()
C1_essai2 = df["C1 (2)"].to_numpy()
C1_essai3 = df["C1(3)"].to_numpy()
d = 8 - distance_diminue

# --- Moyennes et incertitudes ---
C1_moy = np.mean([C1_essai1, C1_essai2, C1_essai3], axis=0)
C1_std = np.std([C1_essai1, C1_essai2, C1_essai3], axis=0, ddof=1)

n = 3
incertitude_d  = 1 / 9
incertitude_C1 = np.sqrt(0.001**2 + (C1_std / np.sqrt(n))**2)

# --- Modèles ---
def C1_model_avec_bord(params, d):
    A, B, C1_bord = params
    return A / (np.minimum(6,d )+ B) + C1_bord

def C1_model_sans_bord(params, d):
    A, B = params
    return A / (np.minimum(6,d )+ B) 

def cout_avec_bord(params, d, C1_data):
    return C1_data - C1_model_avec_bord(params, d)

def cout_sans_bord(params, d, C1_data):
    return C1_data - C1_model_sans_bord(params, d)

# --- Découpage montée / descente ---
montee   = df.iloc[0:16].copy()
descente = df.iloc[16:31].copy()

etapes   = {"Montée": montee, "Descente": descente}
couleurs = {"Montée": "steelblue", "Descente": "tomato"}

params_avec_bord  = {}
params_sans_bord  = {}
residus_avec_bord = {}
residus_sans_bord = {}

# --- Figure 1 : parité ---
fig1, ax1 = plt.subplots(figsize=(6, 6))

for nom, df_etape in etapes.items():
    d_et = 8 - df_etape["Distance_diminué"].to_numpy()

    # Optimisation sur la MOYENNE des 3 essais
    C1_et = np.mean([
        df_etape["C1  pF"].to_numpy(),
        df_etape["C1 (2)"].to_numpy(),
        df_etape["C1(3)"].to_numpy()
    ], axis=0)

    mask  = np.isfinite(d_et) & np.isfinite(C1_et) & (d_et > 0)
    d_et  = d_et[mask]
    C1_et = C1_et[mask]

    x0_avec = [(C1_et.max() - C1_et.min()) * d_et.mean(), 0.1, C1_et.min()]
    res_avec = least_squares(cout_avec_bord, x0_avec,
                             bounds=([0, 0, 0], [np.inf, np.inf, np.inf]),
                             args=(d_et, C1_et), verbose=0)
    params_avec_bord[nom]  = res_avec.x
    residus_avec_bord[nom] = (d_et, res_avec.fun)

    x0_sans = [(C1_et.max() - C1_et.min()) * d_et.mean(), 0.1]
    res_sans = least_squares(cout_sans_bord, x0_sans,
                             bounds=([0, 0], [np.inf, np.inf]),
                             args=(d_et, C1_et), verbose=0)
    params_sans_bord[nom]  = res_sans.x
    residus_sans_bord[nom] = (d_et, res_sans.fun)

    A_avec, B_avec, C1_bord_opt = res_avec.x
    A_sans, B_sans      = res_sans.x

    print(f"\n--- {nom} ---")
    print(f"  Avec bord : A={A_avec:.6f}, B={B_avec:.6f}, C1_bord={C1_bord_opt:.6f} pF")
    print(f"  Sans bord : A={A_sans:.6f}, B={B_sans:.6f}")

    C1_predit = C1_model_avec_bord(res_avec.x, d_et)
    ax1.scatter(C1_predit, C1_et, color=couleurs[nom], edgecolors="white",
                linewidths=0.5, s=60, zorder=5,
                label=f"{nom}  (A={A_avec:.3f}, B={B_avec:.3f}, C1b={C1_bord_opt:.3f})")

lim_vals = [ax1.get_xlim()[0], ax1.get_xlim()[1],
            ax1.get_ylim()[0], ax1.get_ylim()[1]]
lim = (min(lim_vals) - 0.05, max(lim_vals) + 0.05)
ax1.plot(lim, lim, color="gray", linewidth=1.2, linestyle="--", label="y = x (idéal)")
ax1.set_xlim(lim)
ax1.set_ylim(lim)
ax1.set_aspect("equal")
ax1.set_xlabel("C1 modèle (pF)")
ax1.set_ylabel("C1 mesuré (pF)")
ax1.set_title("Parité C1 — montée vs descente")
ax1.legend(fontsize=8)
ax1.grid(True, linestyle="--", alpha=0.4)
fig1.tight_layout()
fig1.savefig("C1_parity_hysteresis.png", dpi=150)

# --- Figure 2 : expérimental vs modèles ---
mask_all = np.isfinite(d) & (d > 0)

mask_aller       = mask_all.copy()
mask_aller[16:]  = False
mask_retour      = mask_all.copy()
mask_retour[:16] = False

d_exp_aller   = d[mask_aller]
C1_exp_aller  = C1_moy[mask_aller]
inc_C1_aller  = incertitude_C1[mask_aller]

d_exp_retour  = d[mask_retour]
C1_exp_retour = C1_moy[mask_retour]
inc_C1_retour = incertitude_C1[mask_retour]

A_aller_avec,  B_aller_avec,  C1_bord_aller  = params_avec_bord["Montée"]
A_retour_avec, B_retour_avec, C1_bord_retour = params_avec_bord["Descente"]
A_aller_sans,  B_aller_sans   = params_sans_bord["Montée"]
A_retour_sans, B_retour_sans  = params_sans_bord["Descente"]

fig2, ax2 = plt.subplots(figsize=(9, 5))

ax2.errorbar(d_exp_aller, C1_exp_aller,
             xerr=incertitude_d, yerr=inc_C1_aller,
             fmt='o-', color="steelblue", capsize=3, linewidth=1,
             label="C1 expérimental — montée")

ax2.errorbar(d_exp_retour, C1_exp_retour,
             xerr=incertitude_d, yerr=inc_C1_retour,
             fmt='o-', color="tomato", capsize=3, linewidth=1,
             label="C1 expérimental — descente")

ax2.plot(d_exp_aller,  C1_model_avec_bord(params_avec_bord["Montée"],   d_exp_aller),
         color="steelblue", linewidth=1.5, linestyle="-.",
         label=f"Avec bord — montée   (A={A_aller_avec:.3f}, B={B_aller_avec:.3f}, C1b={C1_bord_aller:.3f})")

ax2.plot(d_exp_retour, C1_model_avec_bord(params_avec_bord["Descente"], d_exp_retour),
         color="tomato", linewidth=1.5, linestyle="-.",
         label=f"Avec bord — descente (A={A_retour_avec:.3f}, B={B_retour_avec:.3f}, C1b={C1_bord_retour:.3f})")


ax2.set_xlabel("d (mm)")
ax2.set_ylabel("C1 (pF)")
ax2.set_title("C1 expérimental vs modèles (avec / sans effet de bord)")
ax2.legend(fontsize=8)
ax2.grid(True, linestyle="--", alpha=0.4)
fig2.tight_layout()
fig2.savefig("C1_model_vs_exp.png", dpi=150)

# --- Figure 3 : résidus ---
fig3, ax3 = plt.subplots(figsize=(9, 5))

for nom, (d_res, res) in residus_avec_bord.items():
    ax3.scatter(d_res, res, color=couleurs[nom], edgecolors="white",
                linewidths=0.5, s=60, zorder=5,
                label=f"Résidus avec bord — {nom}")

for nom, (d_res, res) in residus_sans_bord.items():
    ax3.scatter(d_res, res, color=couleurs[nom], edgecolors="white",
                linewidths=0.5, s=30, zorder=4,
                label=f"Résidus sans bord — {nom}")

ax3.axhline(0, color="gray", linewidth=1, linestyle="--")
ax3.set_xlabel("d (mm)")
ax3.set_ylabel("Résidus (pF)")
ax3.set_title("Résidus des modèles avec / sans effet de bord")
ax3.legend(fontsize=8)
ax3.grid(True, linestyle="--", alpha=0.4)
fig3.tight_layout()
fig3.savefig("C1_residus.png", dpi=150)

plt.show()