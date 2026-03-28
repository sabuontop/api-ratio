# 🚀 API Ratio Tracker

Une API robuste et modulaire en **Python (FastAPI)** conçue pour scraper automatiquement vos statistiques (Upload, Download, Ratio) depuis divers trackers privés et les exposer pour vos tableaux de bord (Glance, Dashy, etc.) ou pour du monitoring avec **Prometheus**.

---

## 🌟 Points Forts

- **Automatisé** : Connexion automatique via Playwright pour gérer les sessions et le localStorage.
- **Modulaire** : Architecture par "scrappers" permettant d'ajouter facilement de nouveaux trackers.
- **Monitoring natif** : Expose des métriques au format Prometheus sur `/metrics`.
- **Docker-Ready** : Image optimisée (Slim) pour un déploiement ultra-léger et rapide.
- **Sécurisé** : Gestion des identifiants via variables d'environnement (`.env`).

---

## 🛠️ Trackers Supportés

- [x] **C411** (API Auth / Cloudflare compatible)
- [x] **Torr9** (LocalStorage Token Auth)
- [x] **Gemini** (API Key Support)

---

## 🚀 Installation & Déploiement

### Option 1 : Docker Compose (Recommandé)

1. Clonez le dépôt :
   ```bash
   git clone https://github.com/sabuontop/api-ratio.git
   cd api-ratio
   ```

2. Configurez vos accès dans un fichier `.env` à la racine.
3. Lancez le service :
   ```bash
   docker compose up -d --build
   ```

### Option 2 : Installation manuelle

1. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   playwright install chromium --with-deps
   ```

2. Lancez l'API :
   ```bash
   python api.py
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
| `GEMINI_TOKEN` | Votre jeton API pour Gemini-Tracker |
| `REFRESH_INTERVAL_MINUTES` | Fréquence de mise à jour (Défaut: 60 min) |

---

## 👨‍💻 Contribution
Les Pull Requests sont les bienvenues ! Pour ajouter un tracker, créez simplement un nouveau fichier dans le dossier `scrappers/`.
