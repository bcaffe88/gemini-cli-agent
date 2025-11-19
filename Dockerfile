FROM python:3.11-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Configurar Git
RUN git config --global user.name "Gemini Agent" && \
    git config --global user.email "agent@criptopnz.com"

# Instalar dependências Python
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Criar diretório de workspace
RUN mkdir -p /app/workspace

# Dar permissão de execução
RUN chmod +x start.sh

# Expor porta
EXPOSE 8080

# Iniciar aplicação
CMD ["./start.sh"]
