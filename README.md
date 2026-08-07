# API Ratio Tracker

API Python (FastAPI) permettant de récupérer automatiquement vos statistiques de ratio (upload, download, bonus) depuis vos trackers torrent et d'exposer les métriques au format JSON ou Prometheus.

## Trackers supportés

- **C411**
- **Crazy Spirits**
- **Gemini**
- **Generation Free**
- **HD-Space**
- **La Cale**
- **NEXUM**
- **Nostradamus**
- **Redacted**
- **The Old School**
- **Torr9**
- **TR4KER**

## Déploiement Docker

Exemple de `docker-compose.yml` :

```yaml
services:
  scrap-ratio:
    image: sabuontop/api-ratio:latest
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

Démarrage :
```bash
docker compose up -d
```

## Endpoints

- `GET /ratios` : Données formatées en JSON (ratio, upload, download, bonus).
- `GET /metrics` : Exposition Prometheus pour vos dashboards.
- `GET /` : Statut du service.

## Configuration (.env)

| Variable | Description |
| :--- | :--- |
| `TR4KER_TOKEN` | Clé API TR4KER |
| `TR4KER_USER` / `TR4KER_PASS` | Identifiants TR4KER (alternative au token) |
| `TORR9_USER` / `TORR9_PASSWORD` | Identifiants Torr9 |
| `C411_USER` / `C411_PASS` | Identifiants C411 |
| `LACALE_USER` / `LACALE_PASS` | Identifiants La Cale |
| `GEMINI_TOKEN` | Jeton API Gemini |
| `TOS_TOKEN` | Jeton API The Old School |
| `GFREE_TOKEN` | Jeton API Generation Free |
| `RED_APIKEY` | Jeton API Redacted |
| `NEXUM_API_KEY` | Clé API Nexum |
| `HDSPACE_COOKIE` | Cookies HD-Space (`uid=...; pass=...`) |
| `CRAZYSPIRITS_COOKIE` | Cookies CrazySpirits (`uid=...; pass=...`) |
| `NOSTRADAMUS_PRIVATE_KEY` | Clé privée Nostradamus |
| `REFRESH_INTERVAL_MINUTES` | Intervalle de rafraîchissement en minutes (Défaut: 60) |
