FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /usr/src/app

# Instalar dependencias del sistema que pandas necesita (libpq, tzdata, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential gcc && \
    rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalarlos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY main.py .

# Comando por defecto (se sobreescribe desde docker-compose; aquí solo un placeholder)
CMD ["python", "main.py"]
