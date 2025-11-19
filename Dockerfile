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

# Criar usuário para SSH
RUN useradd -ms /bin/bash app

# Criar pastas e permissões
RUN mkdir /home/app/.ssh && chmod 700 /home/app/.ssh

# Copiar app
WORKDIR /app
COPY . .

RUN chmod +x start.sh

EXPOSE 22
CMD ["/app/start.sh"]
