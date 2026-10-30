import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from aiohttp import web

TOKEN_TELEGRAM = "9196191146:AAEv9VZI9m-fGHCkWIGL8rGgX1U-Yj9T-vY"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Coda globale dei comandi in attesa per il PC
comandi_pendenti = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 IA Cloud Attiva! Mandami un comando. Se il PC è spento, lo eseguirà appena si accende.")

async def gestisci_comandi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    testo = update.message.text.lower()
    chat_id = update.message.chat_id

    if "programma" in testo:
        try:
            secondi = int(''.join(filter(str.isdigit, testo)))
        except:
            secondi = 10
        await update.message.reply_text(f"⏰ Promemoria avviato per tra {secondi} secondi.")
        asyncio.create_task(timer_promemoria(context, chat_id, seconds=secondi))
        
    elif any(p in testo for p in ["apri", "chiama", "whatsapp", "messaggio", "calcolo"]):
        comandi_pendenti.append(testo)
        await update.message.reply_text(f"📥 Comando '{testo}' salvato nel cloud. In attesa del PC...")
    else:
        await update.message.reply_text(f"🤖 Ricevuto nel cloud: '{testo}'")

async def timer_promemoria(context, chat_id, seconds):
    await asyncio.sleep(seconds)
    await context.bot.send_message(chat_id=chat_id, text="⏰ Promemoria scaduto!")

# --- SERVER HTTP PER IL PC DI CASA ---
async def handle_pc_request(request):
    global comandi_pendenti
    if comandi_pendenti:
        comandi_da_inviare = list(comandi_pendenti)
        comandi_pendenti.clear()
        return web.json_response({"status": "ok", "comandi": comandi_da_inviare})
    return web.json_response({"status": "ok", "comandi": []})

async def start_server():
    app = web.Application()
    app.router.add_get('/get_commands', handle_pc_request)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("Server HTTP avviato sulla porta 8080")

def main():
    application = Application.builder().token(TOKEN_TELEGRAM).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, gestisci_comandi))
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_server())
    
    print("IA Cloud in esecuzione...")
    application.run_polling()

if __name__ == '__main__':
    main()
