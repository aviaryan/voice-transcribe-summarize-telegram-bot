import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq
from pathlib import Path
import tempfile
from dotenv import load_dotenv
import asyncio

load_dotenv()

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Initialize bot application
async def create_application():
    """Create and configure the bot application."""
    application = (
        Application.builder()
        .token(os.getenv("TELEGRAM_BOT_TOKEN"))
        .build()
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    
    return application

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

async def main():
    """Start the bot."""
    application = await create_application()
    print("Starting bot...")
    await application.initialize()
    await application.start()
    await application.run_polling()
    await application.stop()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped gracefully!")
