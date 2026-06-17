import pandas as pd
import numpy as np
from scipy.optimize import least_squares
import matplotlib.pyplot as plt

# --- Chargement ---
df = pd.read_csv("Book1.csv")

distance_diminue = df["Distance_diminué"].to_numpy()

C2_essai1 = df["C2 avec C1 pF"].to_numpy()
C2_essai2 = df["C2 avce C1 (2)"].to_numpy()
C2_essai3 = df["C2 avce C1 (3)"].to_numpy()

d = 8 - distance_diminue

# --- Moyennes et incertitudes ---
C2_moy = np.mean([C2_essai1, C2_essai2, C2_essai3], axis=0)
C2_std = np.std([C2_essai1, C2_essai2, C2_essai3], axis=0, ddof=1)

n = 3
incertitude_d  = 1 / 9
incertitude_C2 = np.sqrt(0.001**2 + (C2_std / np.sqrt(n))**2)

# --- Modèles ---
def C2_model_avec_bord(params, d):
    A, B, C2_bord = params
    return A / (d + B) + C2_bord



def cout_avec_bord(params, d, C2_data):
    return C2_data - C2_model_avec_bord(params, d) 


# --- Découpage montée / descente ---
montee   = df.iloc[0:16].copy()
descente = df.iloc[16:31].copy()

etapes   = {"Montée": montee, "Descente": descente}
couleurs = {"Montée": "steelblue", "Descente": "tomato"}

params_avec_bord  = {}

residus_avec_bord = {}


# --- Figure 1 : parité ---
fig1, ax1 = plt.subplots(figsize=(6, 6))

for nom, df_etape in etapes.items():
    d_et = 8 - df_etape["Distance_diminué"].to_numpy()

    # Optimisation sur la MOYENNE des 3 essais
    C2_et = np.mean([
        df_etape["C2 avec C1 pF"].to_numpy(),
        df_etape["C2 avce C1 (2)"].to_numpy(),
        df_etape["C2 avce C1 (3)"].to_numpy()
    ], axis=0)

    mask  = np.isfinite(d_et) & np.isfinite(C2_et) & (d_et > 0)
    d_et  = d_et[mask]
    C2_et = C2_et[mask]

    x0_avec = [(C2_et.max() - C2_et.min()) * d_et.mean(), 0.1, C2_et.min()]
    res_avec = least_squares(cout_avec_bord, x0_avec,
                             bounds=([0, 0, 0], [np.inf, np.inf, np.inf]),
                             args=(d_et, C2_et), verbose=0)
    params_avec_bord[nom]  = res_avec.x
    residus_avec_bord[nom] = (d_et, res_avec.fun)

    A_avec, B_avec, C2_bord_opt = res_avec.x

    print(f"\n--- {nom} ---")
    print(f"  Avec bord : A={A_avec:.6f}, B={B_avec:.6f}, C2_bord={C2_bord_opt:.6f} pF")

    C2_predit = C2_model_avec_bord(res_avec.x, d_et)
    ax1.scatter(C2_predit, C2_et, color=couleurs[nom], edgecolors="white",
                linewidths=0.5, s=60, zorder=5,
                label=f"{nom}  (A={A_avec:.3f}, B={B_avec:.3f}, C2b={C2_bord_opt:.3f})")

lim_vals = [ax1.get_xlim()[0], ax1.get_xlim()[1],
            ax1.get_ylim()[0], ax1.get_ylim()[1]]
lim = (min(lim_vals) - 0.05, max(lim_vals) + 0.05)
ax1.plot(lim, lim, color="gray", linewidth=1.2, linestyle="--", label="y = x (idéal)")
ax1.set_xlim(lim)
ax1.set_ylim(lim)
ax1.set_aspect("equal")
ax1.set_xlabel("C2 modèle (pF)")
ax1.set_ylabel("C2 mesuré (pF)")
ax1.set_title("Parité C2 — montée vs descente")
ax1.legend(fontsize=8)
ax1.grid(True, linestyle="--", alpha=0.4)
fig1.tight_layout()
fig1.savefig("C2_parity_hysteresis.png", dpi=150)

# --- Figure 2 : expérimental vs modèles ---
mask_all = np.isfinite(d) & (d > 0)

mask_aller       = mask_all.copy()
mask_aller[16:]  = False
mask_retour      = mask_all.copy()
mask_retour[:16] = False

d_exp_aller   = d[mask_aller]
C2_exp_aller  = C2_moy[mask_aller]
inc_C2_aller  = incertitude_C2[mask_aller]

d_exp_retour  = d[mask_retour]
C2_exp_retour = C2_moy[mask_retour]
inc_C2_retour = incertitude_C2[mask_retour]

A_aller_avec,  B_aller_avec,  C2_bord_aller  = params_avec_bord["Montée"]
A_retour_avec, B_retour_avec, C2_bord_retour = params_avec_bord["Descente"]


fig2, ax2 = plt.subplots(figsize=(9, 5))

ax2.errorbar(d_exp_aller, C2_exp_aller,
             xerr=incertitude_d, yerr=inc_C2_aller,
             fmt='o-', color="steelblue", capsize=3, linewidth=1,
             label="C2 expérimental — montée")

ax2.errorbar(d_exp_retour, C2_exp_retour,
             xerr=incertitude_d, yerr=inc_C2_retour,
             fmt='o-', color="tomato", capsize=3, linewidth=1,
             label="C2 expérimental — descente")

ax2.plot(d_exp_aller,  C2_model_avec_bord(params_avec_bord["Montée"],   d_exp_aller),
         color="steelblue", linewidth=1.5, linestyle="-.",
         label=f"Avec bord — montée   (A={A_aller_avec:.3f}, B={B_aller_avec:.3f}, C2b={C2_bord_aller:.3f})")

ax2.plot(d_exp_retour, C2_model_avec_bord(params_avec_bord["Descente"], d_exp_retour),
         color="tomato", linewidth=1.5, linestyle="-.",
         label=f"Avec bord — descente (A={A_retour_avec:.3f}, B={B_retour_avec:.3f}, C2b={C2_bord_retour:.3f})")



ax2.set_xlabel("d (mm)")
ax2.set_ylabel("C2 (pF)")
ax2.set_title("C2 expérimental vs modèles (avec / sans effet de bord)")
ax2.legend(fontsize=8)
ax2.grid(True, linestyle="--", alpha=0.4)
fig2.tight_layout()
fig2.savefig("C2_model_vs_exp.png", dpi=150)

# --- Figure 3 : résidus ---
fig3, ax3 = plt.subplots(figsize=(9, 5))

for nom, (d_res, res) in residus_avec_bord.items():
    ax3.scatter(d_res, res, color=couleurs[nom], edgecolors="white",
                linewidths=0.5, s=60, zorder=5,
                label=f"Résidus avec bord — {nom}")


ax3.axhline(0, color="gray", linewidth=1, linestyle="--")
ax3.set_xlabel("d (mm)")
ax3.set_ylabel("Résidus (pF)")
ax3.set_title("Résidus des modèles avec / sans effet de bord")
ax3.legend(fontsize=8)
ax3.grid(True, linestyle="--", alpha=0.4)
fig3.tight_layout()
fig3.savefig("C2_residus.png", dpi=150)

plt.show()