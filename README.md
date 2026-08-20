# API Ratio Tracker

API Python (FastAPI) permettant de récupérer automatiquement vos statistiques de ratio (upload, download, bonus) depuis vos trackers torrent et d'exposer les métriques au format JSON ou Prometheus.

## Trackers supportés

- **C411**
- **Crazy Spirits**
- **Gemini**
- **Generation Free**
- **HD-Space**
- **La Cale**
- **Memphis**
- **NEXUM**
- **Nostradamus**
- **Redacted**
- **The Old School**
- **TR4KER**
- **YGG Reborn**

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
- `GET /metrics` : Exposition Prometheus pour vos dashboards (Grafana, etc.).
- `GET /` : Statut du service.

## Configuration (.env)

| Variable | Description |
| :--- | :--- |
| `TR4KER_TOKEN` | Clé API TR4KER |
| `YGGREBORN_COOKIE` | Cookies de session YGG Reborn (`__ygg_sess=...; cf_clearance=...`) |
| `YGGREBORN_USER_AGENT` | User-Agent exact de votre navigateur (requis pour valider `cf_clearance`) |
| `MEMPHIS_USER` / `MEMPHIS_PASS` | Identifiants Memphis |
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

### Note sur les trackers à cookies (YGG Reborn, CrazySpirits, HD-Space)

Certains trackers utilisent des protections anti-bot (Cloudflare Turnstile) ou n'exposent pas d'API ratio publique. Pour ces sites :
1. Connectez-vous sur le site via votre navigateur.
2. Copiez les cookies de session via les outils de développement (F12 -> Application -> Cookies).
3. Renseignez la variable `_COOKIE` dans votre `.env`.
4. Pour YGG Reborn, ajoutez aussi `YGGREBORN_USER_AGENT` avec la valeur de `navigator.userAgent` de votre navigateur.
