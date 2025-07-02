FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Criar diretório para o banco de dados e definir permissões
RUN mkdir -p /app/data && \
    chmod 755 /app/data

# Definir variáveis de ambiente
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/app/data

# Expor a porta 5000
EXPOSE 5000

# Script de inicialização
RUN echo '#!/bin/bash\n\
python -c "from app import criar_tabelas; criar_tabelas()"\n\
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 app:app' > /app/start.sh && \
chmod +x /app/start.sh

CMD ["/app/start.sh"] 