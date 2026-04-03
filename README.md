# 🚀 API Ratio Tracker

Une API robuste et modulaire en **Python (FastAPI)** conçue pour scraper automatiquement vos statistiques (Upload, Download, Ratio) depuis divers trackers privés et les exposer pour vos tableaux de bord (Glance, Dashy, etc.) ou pour du monitoring avec **Prometheus**.

---

## 🌟 Points Forts

- **Prêt à l'emploi** : Images Docker officielles disponibles sur Docker Hub et GHCR.
- **Automatisé** : Connexion automatique via Playwright pour gérer les sessions et le localStorage.
- **2FA / TOTP** : Support optionnel de l'authentification à deux facteurs pour les trackers compatibles.
- **Monitoring natif** : Expose des métriques au format Prometheus sur `/metrics`.
- **Léger** : Image Docker optimisée (Slim) pour un déploiement ultra-léger et rapide.
- **Sécurisé** : Gestion des identifiants via variables d'environnement (`.env`).

---

## 🛠️ Trackers Supportés

- [x] **C411** (API Auth / Auto-Login / **2FA TOTP**)
- [x] **La Cale** (Playwright / Auto-Login / **2FA TOTP**)
- [x] **Torr9** (LocalStorage Token / Bonus inclus)
- [x] **Gemini** (API Key Support)
- [x] **Generation Free** (API Key Support)

---

## 🚀 Installation Rapide (Docker Compose)

C'est la méthode de déploiement la plus simple et la plus rapide.

1. Récupérez le fichier `docker-compose.yml` (ou créez-le) :
   ```yaml
   services:
     scrap-ratio:
       image: ghcr.io/sabuontop/api-ratio:latest # ou sabuontop/api-ratio:latest
       container_name: scrap-ratio-api
       restart: always
       ports:
         - "8679:8679"
       env_file:
         - .env
       volumes:
         - ./config:/app/.config
       environment:
         - CONFIG_DIR=/app/.config
   ```

2. Créez un fichier `.env` avec vos identifiants (voir la section Configuration ci-dessous).
3. Lancez le service :
   ```bash
   docker compose up -d
   ```

---

## 📊 Endpoints de l'API

- **`GET /ratios`** : Retourne les statistiques formatées (Go/To) et le ratio actuel.
- **`GET /metrics`** : Métriques au format Prometheus pour Grafana.
- **`GET /`** : Informations basiques sur l'état de l'API.

---

## ⚙️ Configuration (.env)

| Variable | Description |
| :--- | :--- |
| `TORR9_USER` / `TORR9_PASS` | Vos identifiants pour Torr9 |
| `C411_USER` / `C411_PASS` | Vos identifiants pour C411 |
| `C411_TOTP_SECRET` | *(Optionnel)* Secret TOTP pour la 2FA C411 |
| `LACALE_USER` / `LACALE_PASS` | Vos identifiants pour La Cale |
| `LACALE_TOTP_SECRET` | *(Optionnel)* Secret TOTP pour la 2FA La Cale |
| `GEMINI_TOKEN` | Votre jeton API pour Gemini-Tracker |
| `GFREE_TOKEN` | Votre jeton API pour Generation Free |
| `REFRESH_INTERVAL_MINUTES` | Fréquence de mise à jour (Défaut: 60 min) |

### Exemple de fichier `.env`

```dotenv
# Torr9
TORR9_USER=mon_pseudo
TORR9_PASS=mon_mot_de_passe

# C411
C411_USER=mon_email@example.com
C411_PASS=mon_mot_de_passe
# C411_TOTP_SECRET=MON_SECRET_TOTP  # Décommenter si 2FA activée

# La Cale
LACALE_USER=mon_email@example.com
LACALE_PASS=mon_mot_de_passe
# LACALE_TOTP_SECRET=MON_SECRET_TOTP  # Décommenter si 2FA activée

# Gemini
GEMINI_TOKEN=mon_token_api

# Generation Free
GFREE_TOKEN=mon_token_api

# Général
REFRESH_INTERVAL_MINUTES=60
```

> **Note :** Les variables `*_TOTP_SECRET` sont entièrement optionnelles. Si elles ne sont pas définies, la connexion se fait sans 2FA.

---

## 🔐 Support de la 2FA (TOTP)

Certains trackers proposent une authentification à deux facteurs (2FA) via une application TOTP (Google Authenticator, Authy, etc.).

Pour l'activer, récupérez le **secret TOTP** (clé de base) fourni par le tracker lors de la configuration de la 2FA, puis ajoutez-le dans votre `.env` :

```dotenv
C411_TOTP_SECRET=VOTRE_SECRET_BASE32
LACALE_TOTP_SECRET=VOTRE_SECRET_BASE32
```

Le code TOTP est généré automatiquement à chaque connexion via la librairie [`pyotp`](https://pyauth.github.io/pyotp/).

---

## 👨‍💻 Ajouter un Tracker

Les Pull Requests sont les bienvenues ! Pour ajouter un nouveau tracker, créez simplement un fichier dans `scrappers/` en suivant ce squelette :

```python
import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv
from util import MissingCredentialsError, ScrappingError

load_dotenv()
logger = logging.getLogger()

async def get_stats(headless: bool = True) -> Dict[str, Any]:
    """
    Doit retourner un dict avec au minimum :
      - raw_upload   (int, octets)
      - raw_download (int, octets)
      - bonus        (float, points)
    """
    raise NotImplementedError
```

Le fichier est automatiquement détecté par `util.list_scrappers()` — aucune modification ailleurs n't est nécessaire.
