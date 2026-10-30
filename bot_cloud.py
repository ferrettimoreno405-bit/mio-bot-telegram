import logging
import asyncio
import re
import os
import urllib.request
import json
import urllib.parse
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from gtts import gTTS
from aiohttp import web

TOKEN_TELEGRAM = "9196191146:AAEv9VZI9m-fGHCkWIGL8rGgX1U-Yj9T-vY"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Il tuo database personalizzato (ha sempre la precedenza!)
CONOSCENZA = {
    "chi sei": "Sono la tua Intelligenza Artificiale personale e indipendente, creata da Moreno. Giro interamente sul mio codice Python nel cloud ed eseguo i tuoi comandi binari!",
    "come stai": "Sono attiva al cento per cento nei server cloud, i miei circuiti sono pronti!",
    "ciao": "Ciao Moreno! Sono la tua intelligenza artificiale. Come posso aiutarti sul telefono oggi?",
    "aiuto": "Puoi parlarmi a voce, chiedermi di fare calcoli matematici scrivendo i numeri o farmi qualsiasi domanda su personaggi, storia e concetti!"
}

def cerca_su_wikipedia(query_testo):
    """Cerca su Wikipedia in italiano e restituisce un riassunto elementare di 2 frasi"""
    try:
        # Pulisce la richiesta dell'utente
        argomento = query_testo.lower().replace("chi è", "").replace("cos'è", "").replace("cosa significa", "").replace("parlami di", "").strip()
        argomento_enc = urllib.parse.quote(argomento)
        
        # Chiama l'API ufficiale e pubblica di Wikipedia in italiano
        url = f"https://wikipedia.org{argomento_enc}"
        req = urllib.request.Request(url, headers={'User-Agent': 'BotMoreno/1.0 (moreno@example.com)'})
        
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if 'extract' in data:
                # Estrae solo le prime due frasi del riassunto per non fare un vocale troppo lungo
                frasi = data['extract'].split('.')
                riassunto = ". ".join(frasi[:2]).strip() + "."
                return riassunto
    except:
        pass
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await invia_voce(update, context, "Benvenuto! Sono la tua IA enciclopedica personale indipendente. Chiedimi qualsiasi cosa!")

async def invia_voce(update: Update, context: ContextTypes.DEFAULT_TYPE, testo: str):
    chat_id = update.effective_chat.id
    filename = f"voce_{chat_id}.mp3"
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action="record_voice")
        tts = gTTS(text=testo, lang='it', slow=False)
        tts.save(filename)
        with open(filename, 'rb') as voice_file:
            await context.bot.send_voice(chat_id=chat_id, voice=voice_file)
        os.remove(filename)
    except Exception as e:
        await update.message.reply_text(testo)

async def rispondi_telefono(update: Update, context: ContextTypes.DEFAULT_TYPE):
    testo_utente = update.message.text.strip()
    testo_lower = testo_utente.lower()

    # 1. CONTROLLO SE È UN CALCOLO MATEMATICO
    if any(c in testo_utente for c in ["+", "-", "*", "/", "x", ":"]) or any(char.isdigit() for char in testo_utente):
        espressione = testo_lower.replace("calcola", "").replace("quanto fa", "").replace("x", "*").replace(":", "/").strip()
        espressione = re.sub(r'[^0-9+\-*/().\s]', '', espressione)
        if espressione:
            try:
                risultato = eval(espressione)
                await invia_voce(update, context, f"Il risultato del calcolo è {risultato}")
                return
            except:
                pass

    # 2. CONTROLLO SE L'ARGOMENTO È NEL TUO DATABASE FISSO
    for chiave, risposta in CONOSCENZA.items():
        if chiave in testo_lower:
            await invia_voce(update, context, risposta)
            return

    # 3. CONNESSONE AUTOMATICA A WIKIPEDIA SE NON CONOSCE LA RISPOSTA
    risposta_wiki = cerca_su_wikipedia(testo_utente)
    if risposta_wiki:
        await invia_voce(update, context, risposta_wiki)
        return

    # 4. DEFAULT SE WIKIPEDIA NON TROVA LA PAGINA
    await invia_voce(update, context, "Mi dispiace Moreno, non ho trovato informazioni su questo argomento nemmeno su Wikipedia.")

# --- PORTA PER IL PIANO GRATUITO DI RENDER ---
async def handle_home(request):
    return web.Response(text="IA Online con Wikipedia!")

async def start_server():
    app = web.Application()
    app.router.add_get('/', handle_home)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()

def main():
    application = Application.builder().token(TOKEN_TELEGRAM).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, rispondi_telefono))
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_server())
    
    application.run_polling()

if __name__ == '__main__':
    main()
