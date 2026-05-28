
import logging
import os
import random
import time
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode

# Configuration
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL") # URL du webhook fournie par Vercel

# Remplacez par vos vrais liens de canaux. Pour la génération de liens temporaires via l'API Telegram,
# le bot doit être administrateur de ces canaux avec la permission de gérer les liens d'invitation.
# Pour cet exemple, nous utilisons des liens statiques.
MAIN_CHANNEL_LINKS = {
    "Oasis": "https://t.me/+W1RJoJ4sbev4ZWVh",  # Exemple, à remplacer par vos vrais liens
    # Ajoutez d'autres canaux ici si nécessaire
}

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Dictionnaire pour stocker les utilisateurs en attente de vérification
# user_id: {'question': '...', 'answer': '...', 'timestamp': '...'}
verification_pending = {}

# Dictionnaire pour stocker les liens temporaires générés
# user_id: {'link': '...', 'expiry_time': '...'}
invite_links_generated = {}

async def start(update: Update, context) -> None:
    """Envoie un message de bienvenue et lance la vérification."""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name

    if user_id in verification_pending:
        await update.message.reply_text(
            "Vous êtes déjà en cours de vérification. Veuillez répondre à la question précédente."
        )
        return

    if user_id in invite_links_generated and invite_links_generated[user_id]['expiry_time'] > datetime.now():
        link_info = invite_links_generated[user_id]
        remaining_seconds = int((link_info['expiry_time'] - datetime.now()).total_seconds())
        await update.message.reply_text(
            f"Vos liens d'invitation:\n{link_info['link']}\n\nExpire dans {remaining_seconds} secondes, tapez /start à nouveau pour un nouveau lien."
        )
        return

    await update.message.reply_text(
        f"Bonjour {username}! Bienvenue. Pour accéder aux liens, veuillez passer une petite vérification."
    )
    await send_captcha(update, context)

async def send_captcha(update: Update, context) -> None:
    """Génère et envoie une question de captcha."""
    user_id = update.effective_user.id

    # Type de captcha (math ou culture générale)
    captcha_type = random.choice(["math", "culture"])

    if captcha_type == "math":
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        operator = random.choice(['+', '-', '*'])
        question = f"Combien font {num1} {operator} {num2} ?"
        if operator == '+':
            answer = str(num1 + num2)
        elif operator == '-':
            answer = str(num1 - num2)
        else:  # '*'
            answer = str(num1 * num2)
    else: # culture générale
        questions_culture = [
            {"q": "Quelle est la capitale de la France ?", "a": "Paris"},
            {"q": "Quel est le plus grand océan du monde ?", "a": "Pacifique"},
            {"q": "Combien de continents y a-t-il sur Terre ?", "a": "7"},
        ]
        q_a = random.choice(questions_culture)
        question = q_a["q"]
        answer = q_a["a"]

    verification_pending[user_id] = {
        'question': question,
        'answer': answer.lower(),
        'timestamp': datetime.now()
    }
    await update.message.reply_text(f"Vérification requise:\n{question}\nEnvoyez votre réponse.")

async def verify_captcha(update: Update, context) -> None:
    """Vérifie la réponse du captcha et génère les liens si correct."""
    user_id = update.effective_user.id
    user_response = update.message.text.strip().lower()

    if user_id not in verification_pending:
        await update.message.reply_text("Veuillez taper /start pour commencer la vérification.")
        return

    expected_answer = verification_pending[user_id]['answer']
    question_time = verification_pending[user_id]['timestamp']

    # Optionnel: Limiter le temps pour répondre au captcha
    if datetime.now() - question_time > timedelta(minutes=2): # 2 minutes pour répondre
        del verification_pending[user_id]
        await update.message.reply_text(
            "Le temps de réponse a expiré. Veuillez taper /start pour une nouvelle vérification."
        )
        return

    if user_response == expected_answer:
        del verification_pending[user_id]
        await update.message.reply_text("Vérification réussie! Génération de vos liens d'invitation...")
        await generate_invite_links(update, context)
    else:
        await update.message.reply_text(
            "Mauvaise réponse. Veuillez réessayer. \n" +
            verification_pending[user_id]['question']
        )

async def generate_invite_links(update: Update, context) -> None:
    """Génère et envoie les liens d'invitation temporaires."""
    user_id = update.effective_user.id
    
    # Ici, nous allons simuler la génération de liens temporaires.
    # Dans un cas réel, vous utiliseriez l'API Telegram pour créer de vrais liens d'invitation temporaires.
    # Pour l'instant, nous utilisons les liens des canaux principaux.
    
    links_text = "\n".join([f"{name} :- {link}" for name, link in MAIN_CHANNEL_LINKS.items()])
    
    expiry_time = datetime.now() + timedelta(minutes=10) # Lien valide 10 minutes
    invite_links_generated[user_id] = {
        'link': links_text,
        'expiry_time': expiry_time
    }
    
    remaining_seconds = int((expiry_time - datetime.now()).total_seconds())
    await update.message.reply_text(
        f"Vos liens d'invitation:\n{links_text}\n\nExpire dans {remaining_seconds} secondes, tapez /start à nouveau pour un nouveau lien."
    )


async def webhook_handler(request):
    """Gère les requêtes webhook entrantes."""
    if request.method == "POST":
        update = Update.de_json(await request.json(), application.bot)
        await application.process_update(update)
        return "ok"
    return ""


def main() -> None:
    """Démarre le bot en mode webhook."""
    if not TOKEN:
        logger.error("Le token du bot Telegram n'est pas défini. Veuillez définir la variable d'environnement TELEGRAM_BOT_TOKEN.")
        return
    if not WEBHOOK_URL:
        logger.error("L'URL du webhook n'est pas définie. Veuillez définir la variable d'environnement WEBHOOK_URL.")
        return

    global application # Rendre l'application globale pour le webhook_handler
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, verify_captcha))

    # Configurer le webhook
    application.bot.set_webhook(url=WEBHOOK_URL)

    logger.info("Bot configuré en mode webhook.")


if __name__ == "__main__":
    main()

# Pour Vercel, nous avons besoin d'une fonction exportée qui gère les requêtes HTTP.
# Cette fonction sera appelée par Vercel.
# Nous utilisons une approche simple pour l'intégration avec Vercel.
# Dans un fichier `api/index.py` (ou similaire), vous auriez:
# from bot import application, webhook_handler
#
# async def handler(request):
#     return await webhook_handler(request)

# Pour simplifier, nous allons créer un fichier `api/index.py` séparé pour Vercel.
