import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq
from pathlib import Path
import tempfile
from telegram.request import HTTPXRequest
from fastapi import FastAPI, Request, Response
import json

# Initialize FastAPI app
app = FastAPI()

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Initialize bot application
async def create_application():
    """Create and configure the bot application."""
    application = (
        Application.builder()
        .token(os.getenv("TELEGRAM_BOT_TOKEN"))
        .updater(None)  # No updater needed for webhook
        .build()
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    
    return application

# Store application instance
application = None

@app.on_event("startup")
async def startup():
    """Initialize bot when FastAPI starts."""
    global application
    application = await create_application()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "👋 Hi! I'm a Voice Note Summarizer Bot.\n\n"
        "You can:\n"
        "1. Forward me voice messages\n"
        "2. Send me direct voice recordings\n\n"
        "I'll transcribe them and provide you with both the transcription and a summary!"
    )

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages and voice notes."""
    try:
        # Send initial status
        status_message = await update.message.reply_text("🎵 Processing your voice note...")
        
        # Get voice file
        voice_file = await update.message.voice.get_file()
        
        # Download the voice file to a temporary location
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
            await voice_file.download_to_drive(temp_file.name)
            temp_path = temp_file.name

        # Transcribe using Whisper via Groq
        transcription = await transcribe_audio(temp_path)
        
        # Generate summary using LLama 3 via Groq
        summary = await generate_summary(transcription)
        
        # Send results
        await status_message.edit_text(
            "📝 *Transcription:*\n"
            f"{transcription}\n\n"
            "📌 *Summary:*\n"
            f"{summary}",
            parse_mode='Markdown'
        )
        
        # Cleanup temporary file
        os.unlink(temp_path)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Sorry, an error occurred: {str(e)}")

async def transcribe_audio(file_path: str) -> str:
    """Transcribe audio using Whisper via Groq API."""
    # Note: This is a placeholder. You'll need to implement the actual
    # Groq Whisper API call based on their documentation
    completion = groq_client.chat.completions.create(
        model="whisper-large-v3-turbo",  # Replace with actual Groq Whisper model name
        messages=[
            {"role": "system", "content": "Transcribe the following audio file accurately."},
            {"role": "user", "content": file_path}
        ]
    )
    return completion.choices[0].message.content

async def generate_summary(text: str) -> str:
    """Generate a summary using LLama 3 via Groq API."""
    completion = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # Replace with actual Groq LLama 3 model name
        messages=[
            {"role": "system", "content": "Generate a concise summary of the following text:"},
            {"role": "user", "content": text}
        ]
    )
    return completion.choices[0].message.content

@app.post("/api/webhook")
async def webhook(request: Request):
    """Handle incoming webhook requests from Telegram."""
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return Response(status_code=200)
    except Exception as e:
        return Response(content=str(e), status_code=500)

@app.get("/api/set_webhook")
async def set_webhook():
    """Endpoint to set up the webhook."""
    global application
    
    # Check if application is initialized
    if application is None:
        application = await create_application()
    
    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        return {"error": "WEBHOOK_URL environment variable not set"}
    
    try:
        await application.bot.set_webhook(url=f"{webhook_url}/api/webhook")
        return {"message": "Webhook set successfully"}
    except Exception as e:
        return {"error": str(e)}
