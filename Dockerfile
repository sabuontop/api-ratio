# Utiliser une image Python légère (Debian Bookworm)
FROM python:3.12-slim-bookworm

# Définir le dossier de travail
WORKDIR /app

# Variable d'environnement pour Playwright (important)
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Installation des dépendances système minimales pour Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    && pip install --no-cache-dir playwright \
    && playwright install chromium --with-deps \
    && apt-get purge -y --auto-remove wget gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances du projet
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le projet
COPY . .

# Permissions
RUN mkdir -p .config && chmod 700 .config

EXPOSE 8679

CMD ["python", "api.py"]
