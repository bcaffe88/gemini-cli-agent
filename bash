#!/bin/bash
set -e

# Start SSH
service ssh start

# Criar chave para o Gemini (se não existir)
if [ ! -f "/home/app/.gemini/gemini-config.yaml" ]; then
    mkdir -p /home/app/.gemini
    touch /home/app/.gemini/gemini-config.yaml
fi

echo "🔥 Gemini CLI Agent iniciado!"
echo "👉 Conecte via SSH para começar a usar."
sleep infinity
