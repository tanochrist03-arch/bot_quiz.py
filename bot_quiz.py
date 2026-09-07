import os
import sys
import logging
import threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot import types
from dotenv import load_dotenv

# Charge le fichier .env situe dans le meme dossier que le script
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    logging.critical("La variable d'environnement TELEGRAM_BOT_TOKEN est absente.")
    sys.exit(1)

bot = telebot.TeleBot(TOKEN)

QUIZ_DATA = [
    {
        "question": "Quelle est la capitale politique de la Côte d'Ivoire ?",
        "options": ["Abidjan", "Yamoussoukro", "Bouaké", "San-Pédro"],
        "reponse": 1,
        "anecdote": "Yamoussoukro est la capitale politique depuis 1983, mais Abidjan reste le poumon économique."
    },
    {
        "question": "Quel est le plus grand océan de la planète ?",
        "options": ["Océan Atlantique", "Océan Arctique", "Océan Pacifique", "Océan Indien"],
        "reponse": 2,
        "anecdote": "L'océan Pacifique couvre à lui seul près d'un tiers de la surface de la Terre."
    },
    {
        "question": "En quelle année l'Homme a-t-il marché sur la Lune pour la première fois ?",
        "options": ["1965", "1969", "1972", "1980"],
        "reponse": 1,
        "anecdote": "Neil Armstrong et Buzz Aldrin ont aluni le 20 juillet 1969 avec la mission Apollo 11."
    },
    {
        "question": "Qui a peint la fresque de la Chapelle Sixtine ?",
        "options": ["Léonard de Vinci", "Raphaël", "Michel-Ange", "Donatello"],
        "reponse": 2,
        "anecdote": "Michel-Ange a réalisé cette œuvre majeure à Rome entre 1508 et 1512."
    },
    {
        "question": "Quel élément chimique a pour symbole 'Fe' ?",
        "options": ["Fer", "Fluor", "Francium", "Fermium"],
        "reponse": 0,
        "anecdote": "Le symbole Fe dérive directement du mot latin 'ferrum'."
    }
]

sessions = {}
records = {}

def afficher_question(chat_id):
    session = sessions[chat_id]
    idx = session["index"]
    data = QUIZ_DATA[idx]
    total = len(QUIZ_DATA)

    barre = "🟩" * (idx + 1) + "⬜" * (total - (idx + 1))
    lettres = ["A", "B", "C", "D"]

    texte = (
        f"╭───────────────\n"
        f"│  *DÉFI CULTURE G* 🎓\n"
        f"╰───────────────\n\n"
        f"Progression : {barre} ({idx + 1}/{total})\n"
        f"Score actuel : *{session['score']} pts*\n\n"
        f"📌 *Question {idx + 1} :*\n"
        f"_{data['question']}_\n"
    )

    markup = types.InlineKeyboardMarkup(row_width=2)
    boutons = [
        types.InlineKeyboardButton(text=f"{lettres[i]}. {opt}", callback_data=f"rep_{i}")
        for i, opt in enumerate(data["options"])
    ]
    markup.add(*boutons)

    bot.send_message(chat_id, texte, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['start'])
def menu_depart(message):
    chat_id = message.chat.id
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.row("▶️ Lancer le Quiz", "🏆 Mon Record")
    menu.row("ℹ️ Règles du jeu")

    texte = (
        "👋 *Bienvenue sur QuizMaster Bot !*\n\n"
        "Testez vos connaissances en culture générale.\n"
        "Cliquez sur une option ci-dessous pour démarrer :"
    )
    bot.send_message(chat_id, texte, reply_markup=menu, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text in ["▶️ Lancer le Quiz", "/quiz"])
def demarrer_partie(message):
    chat_id = message.chat.id
    sessions[chat_id] = {"index": 0, "score": 0}
    afficher_question(chat_id)

@bot.message_handler(func=lambda msg: msg.text == "🏆 Mon Record")
def afficher_record(message):
    chat_id = message.chat.id
    record = records.get(chat_id, 0)
    bot.send_message(chat_id, f"🏆 Votre record personnel : *{record} / {len(QUIZ_DATA)}*", parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "ℹ️ Règles du jeu")
def afficher_regles(message):
    texte = (
        "📖 *Règles du Quiz :*\n\n"
        "• 5 questions à choix multiples.\n"
        "• Cliquez sur les boutons pour répondre.\n"
        "• +1 point par réponse exacte.\n"
        "• Une anecdote culturelle après chaque question !"
    )
    bot.send_message(chat_id=message.chat.id, text=texte, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("rep_"))
def gerer_clic_reponse(call):
    chat_id = call.message.chat.id

    if chat_id not in sessions:
        bot.answer_callback_query(call.id, "Session expirée. Relancez le quiz.")
        return

    session = sessions[chat_id]
    data = QUIZ_DATA[session["index"]]
    choix = int(call.data.split("_")[1])

    try:
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
    except Exception as e:
        logging.warning(f"Impossible de supprimer les boutons : {e}")

    if choix == data["reponse"]:
        session["score"] += 1
        bot.send_message(chat_id, f"✅ *Bonne réponse !*\n\n💡 _{data['anecdote']}_", parse_mode="Markdown")
    else:
        bonne_opt = data["options"][data["reponse"]]
        bot.send_message(chat_id, f"❌ *Faux !* La solution était : *{bonne_opt}*\n\n💡 _{data['anecdote']}_", parse_mode="Markdown")

    session["index"] += 1

    if session["index"] < len(QUIZ_DATA):
        afficher_question(chat_id)
    else:
        score = session["score"]
        total = len(QUIZ_DATA)
        if score > records.get(chat_id, 0):
            records[chat_id] = score

        bot.send_message(
            chat_id,
            f"🏁 *Fin du quiz !*\n\nScore : *{score} / {total}*\n\nCliquez sur *▶️ Lancer le Quiz* ci-dessous pour rejouer !",
            parse_mode="Markdown"
        )
        del sessions[chat_id]

    bot.answer_callback_query(call.id)

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ["/healthz", "/"]:
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return

def demarrer_serveur_healthcheck():
    port = int(os.getenv("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    logging.info(f"Serveur Healthcheck actif sur le port {port}")
    server.serve_forever()

if __name__ == "__main__":
    http_thread = threading.Thread(target=demarrer_serveur_healthcheck, daemon=True)
    http_thread.start()

    logging.info("Lancement du polling Telegram...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
    