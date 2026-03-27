# 🚀 Ratio Tracker API (Torr9 & C411)

Ce projet permet de récupérer vos statistiques (ratio, upload, download) sur les trackers privés **Torr9.net** et **C411.org** en utilisant leurs APIs officielles via un serveur FastAPI ou un script en ligne de commande.

## 🛠️ Installation

### 1. Prérequis
Vous devez avoir **Python 3.8+** installé.

### 2. Cloner et installer les dépendances
```bash
# Créer un environnement virtuel (recommandé)
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# ou .\venv\Scripts\activate  # Windows

# Installer les bibliothèques
pip install -r requirements.txt

# Installer les navigateurs Playwright
playwright install chromium --with-deps
```

## ⚙️ Configuration

Le script utilise des jetons (tokens) et des cookies manuels pour plus de stabilité.

### 1. Fichier `.env`
Créez un fichier `.env` à la racine du projet avec vos accès :
```env
TORR9_TOKEN="votre_bearer_token_ici"
C411_USER="pseudo"
C411_PASS="password"
```

### 2. Cookies C411
Pour C411, le script utilise un fichier `c411_cookies.json`. Si le fichier n'existe pas, vous pouvez le créer manuellement au format JSON Playwright avec vos cookies de session (`__Host-c411_session` et `__csrf`).

## 🚀 Utilisation

### Mode API (Serveur FastAPI)
Lancez le serveur pour exposer les statistiques via une API JSON :
```bash
python api.py
```
Les statistiques seront disponibles sur : `http://127.0.0.1:8679/ratios`

### Mode CLI (Ligne de commande)
Utilisez le script `scrap_ratio.py` pour obtenir un affichage rapide dans le terminal :
```bash
# Pour Torr9
python scrap_ratio.py --site torr9

# Pour C411
python scrap_ratio.py --site c411

# Pour les deux
python scrap_ratio.py --site both
```

## ☁️ Déploiement sur VPS (Linux)

Si vous déployez sur un VPS avec Debian/Ubuntu (PEP 668), utilisez impérativement un **venv** :

1.  Suivez les étapes d'installation ci-dessus.
2.  Utilisez **PM2** pour garder l'API active :
    ```bash
    pm2 start api.py --interpreter ./venv/bin/python3 --name "ratio-api"
    ```

## 📝 Notes
- **Torr9** : Le `TORR9_TOKEN` (Bearer) se trouve dans les outils de développement de votre navigateur (Application -> LocalStorage ou Network -> Headers).
- **C411** : Si la connexion automatique échoue, copiez vos cookies de navigateur dans `c411_cookies.json`.

