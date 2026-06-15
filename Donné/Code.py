import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Chargement du CSV
df = pd.read_csv("Book1.csv")

# --- Récupération des colonnes ---
distance_diminue = df["Distance_diminué"].to_numpy()

# Les 3 essais pour C1 (avec C1) et C2 (avec C1)
C1_essai1 = df["C1  pF"].to_numpy()
C1_essai2 = df["C1 (2)"].to_numpy()
C1_essai3 = df["C1(3)"].to_numpy()

C2_essai1 = df["C2 avec C1 pF"].to_numpy()
C2_essai2 = df["C2 avce C1 (2)"].to_numpy()
C2_essai3 = df["C2 avce C1 (3)"].to_numpy()

# --- Calcul de d ---
incertitude_d_diminue = 1/9
d = 8 - distance_diminue
incertitude_d = incertitude_d_diminue  # car d(8-x)/dx = -1, donc même incertitude

# --- Moyennes sur les 3 essais ---
C1_moy = np.mean([C1_essai1, C1_essai2, C1_essai3], axis=0)
C2_moy = np.mean([C2_essai1, C2_essai2, C2_essai3], axis=0)

# Incertitude type A (dispersion entre les 3 essais)
C1_std = np.std([C1_essai1, C1_essai2, C1_essai3], axis=0, ddof=1)
C2_std = np.std([C2_essai1, C2_essai2, C2_essai3], axis=0, ddof=1)

# Incertitude instrumentale donnée : 0,001 sur C2
incertitude_C2_instr = 0.001
incertitude_C1_instr = 0.001  # à ajuster si différente

# Incertitude totale = combinaison quadratique (instrumentale + dispersion/sqrt(3))
n = 3
incertitude_C1 = np.sqrt(incertitude_C1_instr**2 + (C1_std / np.sqrt(n))**2)
incertitude_C2 = np.sqrt(incertitude_C2_instr**2 + (C2_std / np.sqrt(n))**2)

# --- Affichage des valeurs ---
print("d       :", d)
print("C1 moyen:", C1_moy)
print("C2 moyen:", C2_moy)

# --- Graphique avec barres d'erreur ---
plt.figure(figsize=(8, 5))
plt.errorbar(d, C1_moy, xerr=incertitude_d, yerr=incertitude_C1,
             fmt='o-', capsize=3, label="C1 moyen (pF)")
plt.errorbar(d, C2_moy, xerr=incertitude_d, yerr=incertitude_C2,
             fmt='s-', capsize=3, label="C2 moyen (pF)")

plt.xlabel("d = 8 - distance_diminué")
plt.ylabel("Capacité (pF)")
plt.title("C1 et C2 (moyennes sur 3 essais) en fonction de d")
plt.legend()
plt.grid(True)
plt.show()