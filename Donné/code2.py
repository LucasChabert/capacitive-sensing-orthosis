import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

# --- Chargement ---
df = pd.read_csv("Book1.csv")

d_mesure = df["d "].to_numpy()
C1 = df["C1  pF"].to_numpy()
C2 = df["C2 avec C1 pF"].to_numpy()
r = C1 / C2  # rapport C1/C2

# =====================================================
# Modèles candidats
# =====================================================

# Modèle 1 (eq. 3 du rapport) : d = Delta_d / (C1/C2 - 1)
def modele1(r, delta_d):
    return delta_d / (r - 1)

# Modèle 2 (eq. 10 du rapport) : d = A / (C1/C2 - 1), A = alpha*Delta_d
def modele2(r, A):
    return A / (r - 1)

# Modèle 3 : avec offset additif (capacité parasite résiduelle)
def modele3(r, A, B):
    return A / (r - 1) + B

# Modèle 4 : facteur 2 (suggestion "modèle faux d'un facteur 2")
def modele4(r, A):
    return 2 * A / (r - 1)

# Modèle 5 : linéaire simple d = K*C1 + d0 (tel que tenté dans ton tableau)
def modele5(C1, K, d0):
    return K * C1 + d0

# Modèle 6 : loi de puissance d = A * C1^b
def modele6(C1, A, b):
    return A * np.power(C1, b)

# Modèle 7 : hyperbolique pur d = A / C1 + B  (cohérent avec C1 = eps*S/d)
def modele7(C1, A, B):
    return A / C1 + B


# =====================================================
# Ajustement de chaque modèle (least squares)
# =====================================================
modeles = {
    "M1: d = Δd/(C1/C2 - 1)":        (modele1, r,  [1.0]),
    "M2: d = A/(C1/C2 - 1)":         (modele2, r,  [1.0]),
    "M3: d = A/(C1/C2 - 1) + B":     (modele3, r,  [1.0, 0.0]),
    "M4: d = 2A/(C1/C2 - 1)":        (modele4, r,  [1.0]),
    "M5: d = K*C1 + d0":             (modele5, C1, [1.0, 0.0]),
    "M6: d = A*C1^b":                (modele6, C1, [1.0, -1.0]),
    "M7: d = A/C1 + B":              (modele7, C1, [1.0, 0.0]),
}

resultats = []

for nom, (f, x, p0) in modeles.items():
    try:
        popt, _ = curve_fit(f, x, d_mesure, p0=p0, maxfev=10000)
        d_pred = f(x, *popt)
        ss_res = np.sum((d_mesure - d_pred) ** 2)
        ss_tot = np.sum((d_mesure - np.mean(d_mesure)) ** 2)
        r2 = 1 - ss_res / ss_tot
        resultats.append((nom, popt, r2, d_pred, x))
    except Exception as e:
        print(f"{nom} : échec de l'ajustement ({e})")

# Tri par qualité de fit décroissante
resultats.sort(key=lambda t: -t[2])

print("Classement des modèles (R² sur les vraies valeurs de d) :")
for nom, popt, r2, _, _ in resultats:
    print(f"  {nom:35s}  paramètres={np.round(popt,4)}   R²={r2:.4f}")

# =====================================================
# Affichage : d mesuré vs d prédit pour les 3 meilleurs
# =====================================================
plt.figure(figsize=(8, 6))
plt.plot(d_mesure, d_mesure, 'k--', label="y = x (idéal)")

for nom, popt, r2, d_pred, _ in resultats[:3]:
    plt.scatter(d_mesure, d_pred, label=f"{nom} (R²={r2:.3f})")

plt.xlabel("d mesuré (vrai)")
plt.ylabel("d prédit par le modèle")
plt.title("Comparaison des modèles candidats")
plt.legend()
plt.grid(True)
plt.show()

# =====================================================
# Affichage : d mesuré et meilleur modèle vs C1/C2 ou C1
# =====================================================
meilleur_nom, meilleur_popt, meilleur_r2, meilleur_pred, meilleur_x = resultats[0]

ordre = np.argsort(meilleur_x)
plt.figure(figsize=(8, 5))
plt.plot(meilleur_x[ordre], d_mesure[ordre], 'o-', label="d mesuré")
plt.plot(meilleur_x[ordre], meilleur_pred[ordre], 'r-', label=f"{meilleur_nom}")
plt.xlabel("variable du modèle (C1/C2 ou C1)")
plt.ylabel("d")
plt.title("Meilleur modèle trouvé")
plt.legend()
plt.grid(True)
plt.show()