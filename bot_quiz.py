import os
import sys
import random
import logging
import threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot import types
from dotenv import load_dotenv

# Chargement du .env
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

# Image de couverture de haute qualité
LOGO_URL = "https://images.unsplash.com/photo-1606326608606-aa0b62935f2b?w=800&auto=format&fit=crop&q=80"

# Banque de questions de culture générale
QUESTION_BANK = [
    {
        "question": "Quelle est la capitale politique de la Côte d'Ivoire ?",
        "options": ["Abidjan", "Yamoussoukro", "Bouaké", "San-Pédro"],
        "reponse": 1,
        "anecdote": "Yamoussoukro est la capitale politique depuis 1983, mais Abidjan demeure le poumon économique."
    },
    {
        "question": "Quel est le plus grand océan de la Terre ?",
        "options": ["Océan Atlantique", "Océan Arctique", "Océan Pacifique", "Océan Indien"],
        "reponse": 2,
        "anecdote": "L'océan Pacifique couvre près d'un tiers de la surface de la planète."
    },
    {
        "question": "En quelle année l'Homme a-t-il marché sur la Lune pour la première fois ?",
        "options": ["1965", "1969", "1972", "1980"],
        "reponse": 1,
        "anecdote": "Neil Armstrong et Buzz Aldrin ont aluni le 20 juillet 1969 lors de la mission Apollo 11."
    },
    {
        "question": "Qui a peint la fresque du plafond de la Chapelle Sixtine ?",
        "options": ["Léonard de Vinci", "Raphaël", "Michel-Ange", "Donatello"],
        "reponse": 2,
        "anecdote": "Michel-Ange a réalisé cette œuvre majeure entre 1508 et 1512 sous commission papale."
    },
    {
        "question": "Quel élément chimique a pour symbole atomique 'Fe' ?",
        "options": ["Fer", "Fluor", "Francium", "Fermium"],
        "reponse": 0,
        "anecdote": "Le symbole 'Fe' dérive directement de son nom latin 'ferrum'."
    },
    {
        "question": "Quel est le plus long fleuve d'Afrique ?",
        "options": ["Le Nil", "Le Congo", "Le Niger", "Le Zambèze"],
        "reponse": 0,
        "anecdote": "Le Nil s'étend sur environ 6 650 km à travers 11 pays africains."
    },
    {
        "question": "Quelle est la monnaie officielle du Japon ?",
        "options": ["Le Yuan", "Le Won", "Le Yen", "Le Ringgit"],
        "reponse": 2,
        "anecdote": "Le Yen a été officiellement adopté comme unité monétaire en 1871 lors de l'ère Meiji."
    },
    {
        "question": "Quel édifice ivoirien compte parmi les plus grandes basiliques au monde ?",
        "options": ["Saint-Pierre", "Notre-Dame de la Paix", "Sainte-Sophie", "Sacré-Cœur"],
        "reponse": 1,
        "anecdote": "La Basilique Notre-Dame de la Paix de Yamoussoukro a été consacrée en 1990."
    },
    {
        "question": "Quel organe humain consomme à lui seul environ 20 % de notre énergie ?",
        "options": ["Le foie", "Le cœur", "Le cerveau", "Les reins"],
        "reponse": 2,
        "anecdote": "Bien qu'il ne représente que 2 % du poids corporel, le cerveau consomme l'essentiel du glucose."
    },
    {
        "question": "Quel écrivain a composé 'Roméo et Juliette' et 'Hamlet' ?",
        "options": ["Molière", "William Shakespeare", "Victor Hugo", "Oscar Wilde"],
        "reponse": 1,
        "anecdote": "Shakespeare a rédigé Roméo et Juliette vers la fin du XVIe siècle."
    },
    {
        "question": "Quel métal offre la conductivité électrique la plus élevée ?",
        "options": ["Le Cuivre", "L'Or", "L'Argent", "L'Aluminium"],
        "reponse": 2,
        "anecdote": "L'argent est le meilleur conducteur absolu, mais le cuivre est préféré pour son coût abordable."
    },
    {
        "question": "En quelle année s'est tenue la première Coupe du Monde de football ?",
        "options": ["1926", "1930", "1934", "1938"],
        "reponse": 1,
        "anecdote": "Cette compétition inaugurale s'est jouée en Uruguay en 1930."
    },
    {
        "question": "Quel est le sommet le plus élevé d'Afrique ?",
        "options": ["Mont Kenya", "Kilimandjaro", "Mont Cameroun", "Mont Stanley"],
        "reponse": 1,
        "anecdote": "Le Kilimandjaro culmine à 5 895 mètres d'altitude en Tanzanie."
    },
    {
        "question": "Quelle planète effectue sa rotation complète en moins de 10 heures ?",
        "options": ["Mars", "Jupiter", "Saturne", "Mercure"],
        "reponse": 1,
        "anecdote": "Jupiter possède la rotation sur elle-même la plus rapide du système solaire."
    },
    {
        "question": "Qui a élaboré la théorie de la relativité restreinte en 1905 ?",
        "options": ["Isaac Newton", "Albert Einstein", "Niels Bohr", "Max Planck"],
        "reponse": 1,
        "anecdote": "Albert Einstein a redéfini notre vision du temps et de l'espace avec cette théorie."
    }
]

sessions = {}
records = {}
QUESTIONS_PAR_MANCHE = 5

def attribuer_rang(score, total):
    ratio = score / total
    if ratio == 1.0:
        return "🏆 Grand Maître Suprême"
    elif ratio >= 0.8:
        return "🎖️ Érudit d'Élite"
    elif ratio >= 0.6:
        return "📚 Connaisseur Averti"
    return "🌱 Novice Curieux"

def afficher_question(chat_id):
    session = sessions[chat_id]
    idx = session["index"]
    data = session["questions"][idx]
    total = len(session["questions"])

    barre = "🟩" * (idx + 1) + "⬜" * (total - (idx + 1))
    lettres = ["A", "B", "C", "D"]

    texte = (
        f"┌─── 🎓 *QUIZMASTER ELITE* ───\n"
        f"│ Progression : *{idx + 1}/{total}*  {barre}\n"
        f"│ Score actuel : *{session['score']} pts*\n"
        f"└───────────────────────\n\n"
        f"📌 *Question {idx + 1} :*\n"
        f"_{data['question']}_\n"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, opt in enumerate(data["options"]):
        markup.add(types.InlineKeyboardButton(text=f"{lettres[i]} │ {opt}", callback_data=f"rep_{i}"))

    bot.send_message(chat_id, texte, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['start'])
def menu_depart(message):
    chat_id = message.chat.id
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    menu.add("▶️ Lancer le Défi", "🏆 Mon Record", "ℹ️ Guide & Règles")

    legende = (
        "╔═══════════════════════╗\n"
        "   🏛️  *QUIZMASTER BOT*  🏛️\n"
        "╚═══════════════════════╝\n\n"
        "Évaluez votre culture générale sur 5 questions aléatoires !\n\n"
        "👇 _Faites votre choix ci-dessous :_"
    )

    try:
        bot.send_photo(chat_id, photo=LOGO_URL, caption=legende, reply_markup=menu, parse_mode="Markdown")
    except Exception as e:
        logging.warning(f"Erreur envoi visuel : {e}")
        bot.send_message(chat_id, legende, reply_markup=menu, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text in ["▶️ Lancer le Défi", "/quiz"])
def demarrer_partie(message):
    chat_id = message.chat.id
    pool = random.sample(QUESTION_BANK, min(QUESTIONS_PAR_MANCHE, len(QUESTION_BANK)))
    sessions[chat_id] = {
        "questions": pool,
        "index": 0,
        "score": 0
    }
    afficher_question(chat_id)

@bot.message_handler(func=lambda msg: msg.text == "🏆 Mon Record")
def afficher_record(message):
    chat_id = message.chat.id
    record = records.get(chat_id, 0)
    titre = attribuer_rang(record, QUESTIONS_PAR_MANCHE) if record > 0 else "Aucun quiz complété"

    texte = (
        f"📊 *TABLEAU PERSONNEL*\n\n"
        f"• Meilleur score : *{record} / {QUESTIONS_PAR_MANCHE}*\n"
        f"• Rang actuel : *{titre}*\n\n"
        f"_Rejouez une manche pour tenter de devenir Grand Maître Suprême !_"
    )
    bot.send_message(chat_id, texte, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "ℹ️ Guide & Règles")
def afficher_regles(message):
    texte = (
        "📜 *RÈGLES DU DÉFI*\n\n"
        f"• *{QUESTIONS_PAR_MANCHE} questions* aléatoires à chaque session.\n"
        "• Validez vos choix en cliquant sur les boutons.\n"
        "• *+1 point* par réponse juste.\n"
        "• Une anecdote explicative détaillée est fournie à chaque question.\n"
        "• Votre record est automatiquement sauvegardé !"
    )
    bot.send_message(chat_id=message.chat.id, text=texte, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("rep_"))
def gerer_clic_reponse(call):
    chat_id = call.message.chat.id

    if chat_id not in sessions:
        bot.answer_callback_query(call.id, "Session expirée. Relancez une partie.")
        return

    session = sessions[chat_id]
    data = session["questions"][session["index"]]
    choix = int(call.data.split("_")[1])

    try:
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
    except Exception as e:
        logging.warning(f"Impossible de masquer le clavier : {e}")

    if choix == data["reponse"]:
        session["score"] += 1
        bot.send_message(chat_id, f"✅ *EXCELLENT !*\n\n💡 _{data['anecdote']}_", parse_mode="Markdown")
    else:
        bonne_opt = data["options"][data["reponse"]]
        bot.send_message(chat_id, f"❌ *RÉPONSE INCORRECTE*\n\nLa bonne réponse était : *{bonne_opt}*\n\n💡 _{data['anecdote']}_", parse_mode="Markdown")

    session["index"] += 1

    if session["index"] < len(session["questions"]):
        afficher_question(chat_id)
    else:
        score = session["score"]
        total = len(session["questions"])
        if score > records.get(chat_id, 0):
            records[chat_id] = score

        titre = attribuer_rang(score, total)
        texte_fin = (
            f"🎯 *DÉFI TERMINÉ !*\n\n"
            f"Résultat final : *{score} / {total}*\n"
            f"Titre obtenu : *{titre}*\n\n"
            f"Cliquez sur *▶️ Lancer le Défi* pour battre votre record !"
        )
        bot.send_message(chat_id, texte_fin, parse_mode="Markdown")
        del sessions[chat_id]

    bot.answer_callback_query(call.id)

# Serveur de santé pour Railway
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
