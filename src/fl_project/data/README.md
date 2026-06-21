# Dataset CIC-IDS2018

Ce dataset n'est pas inclus dans le dépôt pour des raisons de taille.

## Téléchargement

1. Créez un compte sur [Kaggle](https://www.kaggle.com)
2. Téléchargez votre fichier `kaggle.json` depuis votre compte (Settings → API → Create New Token)
3. Placez `kaggle.json` dans le dossier `~/.kaggle/` et exécutez :

```bash
pip install kaggle
mkdir -p ~/.kaggle
cp ~/Téléchargements/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
kaggle datasets download -d solarmainframe/ids-intrusion-csv
unzip ids-intrusion-csv.zip -d src/fl_project/data/
