# SICAI - Sistema Inteligente de Cadeia de Custódia com IA
# Dockerfile para o Pipeline de Engenharia de Dados e Worker de Extração

FROM python:3.11-slim

# Variáveis de ambiente para Python otimizado em containers
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Instalação de utilitários do sistema operacional
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalação das dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Cópia do código-fonte e configurações
COPY src/ /app/src/
COPY tests/ /app/tests/
COPY dbt/ /app/dbt/
COPY pytest.ini /app/pytest.ini

# Ponto de entrada padrão: validação da suíte de testes
CMD ["pytest", "-v"]
