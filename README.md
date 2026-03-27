# 🚀 Tracker Ratio API (Torr9 & C411)

Une API légère et autonome construite avec **FastAPI** et **Playwright** pour récupérer vos statistiques (ratio, upload, download) sur les trackers privés Torr9 et C411. 

Ce projet est conçu pour être intégré facilement dans des tableaux de bord comme **Glance**, **Homepage** ou **Dashy**.

---

## ✨ Caractéristiques

- **Connexion Automatisée** : Le script se connecte tout seul à Torr9 et C411 en utilisant vos identifiants. Plus besoin de copier-coller des cookies ou des tokens manuellement !
- **Gestion des Sessions** : Rafraîchissement automatique des tokens JWT expirés et persistance des cookies.
- **Mise à jour en Arrière-plan** : Utilise un ordonnanceur (`APScheduler`) pour mettre à jour les données toutes les heures sans ralentir les requêtes API.
- **Formatage Intelligent** : Les données de taille (Go, To) sont converties automatiquement pour une lecture humaine.
- **Dashboard Ready** : Sortie JSON propre prête pour n'importe quel widget `custom-api`.

---

## 🛠️ Installation

### 1. Prérequis
Assurez-vous d'avoir Python 3.9+ installé.

```bash
# Cloner le projet
git clone https://github.com/sabuontop/api-ratio.git
cd api-ratio

# Créer et activer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
.\venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Installer les navigateurs Playwright
playwright install chromium
```

### 2. Configuration (.env)
Créez un fichier `.env` à la racine du projet :

```env
# Torr9
TORR9_USER="votre_pseudo"
TORR9_PASSWORD="votre_mot_de_passe"

# C411
C411_USER="votre_pseudo"
C411_PASS="votre_mot_de_passe"
```

---

## 🚀 Utilisation

### Lancer l'API (Serveur)
```bash
python api.py
```
L'API sera disponible sur `http://<VOTRE_IP>:8679/ratios`.

### Utiliser le script ponctuel
Pour voir vos stats rapidement dans le terminal :
```bash
python scrap_ratio.py --site both
```

---

## 🛡️ Sécurité & Recommandations

- **Confidentialité** : Ne partagez jamais votre fichier `.env` ou les fichiers `.json/.txt` générés (cookies/tokens).
- **Abus** : Le script est configuré pour rafraîchir les données toutes les heures. Ne réduisez pas trop cet intervalle pour éviter d'être banni par les trackers pour "scraping excessif".
- **Déploiement VPS** : Il est recommandé d'utiliser **PM2** pour garder l'API active en permanence :
  ```bash
  pm2 start api.py --name "ratio-api" --interpreter ./venv/bin/python
  ```

---
*Réalisé avec ❤️ pour la communauté self-hosted.*
