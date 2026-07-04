# Variantes de firmware

Le firmware compilé par PlatformIO est `../src/main.cpp` (capteur de pression,
mesure différentielle C1/C2). Ce dossier archive les autres versions
développées pendant le stage — pour en utiliser une, remplacer le contenu de
`src/main.cpp` :

| Fichier | Rôle |
|---|---|
| `main_simple.cpp` | Lecture brute d'une seule capacité (prise en main FDC1004) |
| `main_v2.cpp` | Variante de la mesure différentielle |
| `main_DL.cpp` | Variante avec distinction charge/décharge |
| `position.cpp` | Capteur de position (électrodes triangulaires, ratio C1/(C1+C2)) |
| `position_affine.cpp` | Capteur de position avec calibration affine x = aR + b |
