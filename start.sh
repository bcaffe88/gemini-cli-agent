#!/bin/bash
set -e

echo "🤖 =========================================="
echo "🤖 Gemini Autonomous Agent"
echo "🤖 By CriptoPNZ"
echo "🤖 =========================================="

# Verificar variáveis de ambiente
if [ -z "$GITHUB_TOKEN" ]; then
    echo "⚠️  GITHUB_TOKEN não configurado!"
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  GEMINI_API_KEY não configurado!"
fi

# Criar diretórios necessários
mkdir -p /app/workspace
mkdir -p /app/templates
mkdir -p /app/static

echo ""
echo "✅ Ambiente configurado"
echo "🌐 Iniciando servidor web..."
echo ""

# Iniciar aplicação Flask com Gunicorn
exec gunicorn --bind 0.0.0.0:${PORT:-8080} \
              --workers 2 \
              --timeout 600 \
              --access-logfile - \
              --error-logfile - \
              web_interface:app
