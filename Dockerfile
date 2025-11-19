FROM python:3.11-slim

# Instalar dependências
RUN apt-get update && apt-get install -y \
    curl \
    openssh-server \
    git \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório necessário do SSH
RUN mkdir -p /var/run/sshd

# Instalar Gemini CLI
RUN pip install --upgrade pip
RUN pip install google-genai

# Criar usuário e senha
RUN useradd -ms /bin/bash app && echo "app:app" | chpasswd

# Ajustar SSHD para permitir login
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# Copiar app
WORKDIR /app
COPY . .

RUN chmod +x start.sh

EXPOSE 22
CMD ["/app/start.sh"]
