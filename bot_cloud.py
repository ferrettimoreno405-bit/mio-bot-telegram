import logging
import asyncio
import re
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from gtts import gTTS

# Il tuo token ufficiale di Telegram
TOKEN_TELEGRAM = "9196191146:AAHnD-DuIEchd34MIWVqpDqvQLDFphBs504"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- IL DATABASE DELLE CONOSCENZE DELLA TUA IA ---
# Puoi allungare questo elenco inserendo nuove domande e risposte!
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
    testo_benvenuto = "Benvenuto! Sono la tua IA personale indipendente e ora posso anche parlarti! Chiedimi qualcosa."
    await invia_voce(update, context, testo_benvenuto)

async def invia_voce(update: Update, context: ContextTypes.DEFAULT_TYPE, testo: str):
    """Funzione che trasforma il testo in un file vocale e lo invia su Telegram"""
    chat_id = update.effective_chat.id
    filename = f"voce_{chat_id}.mp3"
    
    try:
        # Mostra l'effetto "sta registrando un audio..." su Telegram
        await context.bot.send_chat_action(chat_id=chat_id, action="record_voice")
        
        # Genera l'audio in italiano
        tts = gTTS(text=testo, lang='it', slow=False)
        tts.save(filename)
        
        # Invia il file vocale in chat
        with open(filename, 'rb') as voice_file:
            await context.bot.send_voice(chat_id=chat_id, voice=voice_file)
            
        # Rimuove il file temporaneo dal server per non sprecare spazio
        os.remove(filename)
    except Exception as e:
        logging.error(f"Errore nella generazione della voce: {e}")
        # Invia comunque il testo se la voce fallisce
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
                risposta_calcolo = f"Il risultato del calcolo è {risultato}"
                await invia_voce(update, context, risposta_calcolo)
                return
            except:
                pass

    # 2. CONTROLLO SE L'ARGOMENTO È NEL DATABASE
    for chiave, risposta in CONOSCENZA.items():
        if chiave in testo_lower:
            await invia_voce(update, context, risposta)
            return

    # 3. RISPOSTA DI DEFAULT SE NON TROVA L'ARGOMENTO
    risposta_default = f"Ho ricevuto il tuo messaggio. Non ho ancora questa informazione nel mio database delle conoscenze."
    await invia_voce(update, context, risposta_default)

def main():
    application = Application.builder().token(TOKEN_TELEGRAM).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, rispondi_telefono))
    
    print("IA Telefono Vocale avviata...")
    application.run_polling()

if __name__ == '__main__':
    main()
