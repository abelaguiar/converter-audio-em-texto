# Usar imagem Python 3.11
FROM python:3.11

WORKDIR /app

# Instalar dependências de sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus0 \
    libopus-dev \
    pkg-config \
    git \
    && rm -rf /var/lib/apt/lists/*

# Atualizar pip
RUN pip install --upgrade pip setuptools wheel

# Copiar e instalar requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Criar diretório de modelos
RUN mkdir -p /app/models

# Criar diretórios
RUN mkdir -p /app/uploads

# Copiar aplicação
COPY backend/*.py ./
COPY frontend/ /app/frontend/

# Volume para uploads
VOLUME ["/app/uploads"]

# Expor porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Comando para iniciar a aplicação
CMD ["python", "main.py"]
