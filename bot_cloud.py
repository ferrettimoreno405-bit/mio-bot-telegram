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

TOKEN_TELEGRAM = "9196191146:AAFGba6ibA1EIg9sg9C78DgT6Ih5kLhdcDM"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Database fisso personalizzato
CONOSCENZA = {
    "chi sei": "Sono la tua Intelligenza Artificiale personale e indipendente, creata da Moreno. Giro interamente sul mio codice Python nel cloud ed eseguo i tuoi comandi binari!",
    "come stai": "Sono attiva al cento per cento nei server cloud, i miei circuiti sono pronti!",
    "ciao": "Ciao Moreno! Sono la tua intelligenza artificiale. Come posso aiutarti sul telefono oggi?",
    "aiuto": "Puoi chiedermi il meteo dicendo 'meteo domani', farmi domande su animali o concetti, oppure chiedermi di fare calcoli!"
}

def cerca_su_wikipedia(query_testo):
    """Cerca su Wikipedia in italiano e restituisce le prime due frasi della definizione"""
    try:
        argomento = query_testo.lower().replace("chi è", "").replace("cos'è", "").replace("cosa significa", "").replace("parlami di", "").replace("quando fanno", "").strip()
        
        if "gallin" in query_testo.lower() and "uov" in query_testo.lower():
            argomento = "Gallina"
            
        argomento_enc = urllib.parse.quote(argomento.capitalize())
        url = f"https://wikipedia.org{argomento_enc}"
        req = urllib.request.Request(url, headers={'User-Agent': 'BotMoreno/1.0'})
        
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if 'extract' in data:
                frasi = data['extract'].split('.')
                riassunto = ". ".join(frasi[:2]).strip() + "."
                return riassunto
    except Exception as e:
        logging.error(f"Errore Wiki: {e}")
    return None

def prendi_meteo():
    """Recupera il meteo tramite coordinate geografiche pubbliche (Taranto)"""
    try:
        url = "https://open-meteo.com"
        req = urllib.request.Request(url, headers={'User-Agent': 'BotMoreno/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            
            temp_max = data['daily']['temperature_2m_max'][1]
            temp_min = data['daily']['temperature_2m_min'][1]
            code = data['daily']['weathercode'][1]
            
            # Controllo dei codici senza usare liste numeriche per evitare bug di testo
            if code == 0:
                stato = "sereno"
            elif code < 4:
                stato = "parzialmente nuvoloso"
            elif code < 50:
                stato = "nebbioso"
            elif code < 70:
                stato = "piovoso"
            elif code < 85:
                stato = "nevoso"
            else:
                stato = "temporalesco"
            
            return f"Previsioni meteo per domani nella tua zona: il tempo sarà principalmente {stato}. Si prevede una temperatura massima di {temp_max} gradi e una minima di {temp_min} gradi."
    except Exception as e:
        logging.error(f"Errore Meteo: {e}")
    return "Mi dispiace Moreno, al momento non sono riuscita a connettermi al servizio meteo satellitare."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await invia_voce(update, context, "Benvenuto! Sono la tua IA enciclopedica e meteo personale indipendente. Chiedimi pure che tempo farà domani o qualsiasi altra curiosità!")

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

    if "meteo" in testo_lower or "tempo farà" in testo_lower or "pioggia" in testo_lower:
        risposta_meteo = prendi_meteo()
        await invia_voce(update, context, respuesta_meteo=risposta_meteo)
        return

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

    for chiave, respuesta in CONOSCENZA.items():
        if chiave in testo_lower:
            await invia_voce(update, context, respuesta)
            return

    risposta_wiki = cerca_su_wikipedia(testo_utente)
    if risposta_wiki:
        await invia_voce(update, context, risposta_wiki)
        return

    await invia_voce(update, context, "Mi dispiace Moreno, non ho trovato informazioni precise su questo argomento nel mio cervello locale o su Wikipedia.")

async def handle_home(request):
    return web.Response(text="IA Online con Wikipedia e Meteo!")

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
