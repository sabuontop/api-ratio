# 🚀 API Ratio Tracker

Une API robuste et modulaire en **Python (FastAPI)** conçue pour scraper automatiquement vos statistiques (Upload, Download, Ratio) depuis divers trackers privés et les exposer pour vos tableaux de bord (Glance, Dashy, etc.) ou pour du monitoring avec **Prometheus**.

---

## 🌟 Points Forts

- **Prêt à l'emploi** : Images Docker officielles disponibles sur Docker Hub et GHCR.
- **Automatisé** : Connexion automatique via Playwright pour gérer les sessions et le localStorage.
- **Monitoring natif** : Expose des métriques au format Prometheus sur `/metrics`.
- **Léger** : Image Docker optimisée (Slim) pour un déploiement ultra-léger et rapide.
- **Sécurisé** : Gestion des identifiants via variables d'environnement (`.env`).

---

## 🛠️ Trackers Supportés

- [X] **C411** (API Auth / Auto-Login)
- [X] **Torr9** (LocalStorage Token / Bonus inclus)
- [X] **Gemini** (API Key Support)
- [X] **Generation Free** (API Key Support)
- [X] **Crazy Spirits** (Credentials)
- [X] **Nostradamus** (Private key)
- [X] **TheOldSchool** (API TOKEN)
- [X] **La Cale** (Credentials)
- [X] **Redacted** (API TOKEN)
- [X] **HD-Space** (Credentials)

---

## 🚀 Installation Rapide (Docker Compose)

C'est la méthode de déploiement la plus simple et la plus rapide.

1. Récupérez le fichier `docker-compose.yml` (ou créez-le) :
   ```yaml
   services:
     scrap-ratio:
       image: sabuontop/api-ratio:latest # ou ghcr.io/sabuontop/api-ratio:latest
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
| `TORR9_USER` / `PASS` | Vos identifiants pour Torr9 |
| `C411_USER` / `PASS` | Vos identifiants pour C411 |
| `LACALE_USER` / `PASS` | Vos identifiants pour La Cale |
| `GEMINI_TOKEN` | Votre jeton API pour Gemini-Tracker |
| `TOS_TOKEN` | Votre jeton API pour The Old School |
| `GFREE_TOKEN` | Votre jeton API pour Generation Free |
| `RED_APIKEY` | Votre jeton API pour Redacted |
| `HDSPACE_COOKIE` | Vos cookies 'pass' et 'uid' HD-Space |
| `CRAZYSPIRITS_COOKIE` | Vos cookies 'pass' et 'uid' CrazySpirits |
| `NOSTRADAMUS_PRIVATE_KEY` | Votre jeton API pour Nostradamus |
| `REFRESH_INTERVAL_MINUTES` | Fréquence de mise à jour (Défaut: 60 min) |

---

## 👨‍💻 Contribution
Les Pull Requests sont les bienvenues ! Pour ajouter un tracker, créez simplement un nouveau fichier dans le dossier `scrappers/`.
