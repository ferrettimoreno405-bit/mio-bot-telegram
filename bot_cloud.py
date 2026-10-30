import logging
import asyncio
import re
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from gtts import gTTS
from aiohttp import web

TOKEN_TELEGRAM = "9196191146:AAEv9VZI9m-fGHCkWIGL8rGgX1U-Yj9T-vY"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

CONOSCENZA = {
    "chi sei": "Sono la tua Intelligenza Artificiale personale e indipendente, creata da Moreno. Giro interamente sul mio codice Python nel cloud ed eseguo i tuoi comandi binari!",
    "come stai": "Sono attiva al cento per cento nei server cloud, i miei circuiti sono pronti!",
    "ciao": "Ciao Moreno! Sono la tua intelligenza artificiale. Come posso aiutarti sul telefono oggi?",
    "storia": "La storia è fantastica! L'Impero Romano è iniziato ufficialmente nel ventisette avanti Cristo con Augusto.",
    "scienza": "La scienza ci spiega il mondo. Sapevi che la luce viaggia a circa trecentomila chilometri al secondo?",
    "geografia": "Il nostro pianeta è immenso. La capitale dell'Italia è Roma, mentre la montagna più alta del mondo è l'Everest!",
    "aiuto": "Puoi parlarmi a voce, chiedermi di fare calcoli matematici scrivendo i numeri o chiedermi di argomenti come storia, scienza e geografia!"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await invia_voce(update, context, "Benvenuto! Sono la tua IA personale indipendente e ora posso anche parlarti! Chiedimi qualcosa.")

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

    for chiave, risposta in CONOSCENZA.items():
        if chiave in testo_lower:
            await invia_voce(update, context, risposta)
            return

    await invia_voce(update, context, "Ho ricevuto il tuo messaggio. Non ho ancora questa informazione nel mio database delle conoscenze.")

# --- PORTA FINTA PER INGANNARE RENDER GRATIS ---
async def handle_home(request):
    return web.Response(text="IA Online!")

async def start_server():
    app = web.Application()
    app.router.add_get('/', handle_home)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000) # Render usa la porta 10000 di default
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
