#!/usr/bin/env bash
set -e

echo "=== Veille Immobilière — Installation ==="

python3 -m venv .venv
source .venv/bin/activate

pip install -q --upgrade pip
pip install -q -r requirements.txt
playwright install chromium --with-deps 2>/dev/null || true

if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "⚠️  Édite le fichier .env et remplis :"
    echo "   TELEGRAM_BOT_TOKEN  → créer bot via @BotFather"
    echo "   TELEGRAM_CHAT_ID    → ton ID via @userinfobot"
    echo "   EMAIL_SENDER        → ton email Gmail"
    echo "   EMAIL_PASSWORD      → mot de passe d'application Gmail"
    echo ""
fi

echo "=== Installation terminée ==="
echo "Lance la veille avec : source .venv/bin/activate && python main.py"
