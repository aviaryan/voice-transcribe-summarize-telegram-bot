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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    print(f"Received start command from user: {update.effective_user.id}")
    user_name = update.effective_user.first_name
    try:
        await update.message.reply_text(
            f"👋 Hi {user_name}! I'm a Voice Note Summarizer Bot.\n\n"
            "You can:\n"
            "1. Forward me voice messages\n"
            "2. Send me direct voice recordings\n\n"
            "I'll transcribe them and provide you with both the transcription and a summary!"
        )
        print(f"Sent welcome message to user: {update.effective_user.id}")
    except Exception as e:
        print(f"Error in start handler: {str(e)}")

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
    # completion = groq_client.chat.completions.create(
    #     model="whisper-large-v3-turbo",  # Replace with actual Groq Whisper model name
    #     messages=[
    #         {"role": "system", "content": "Transcribe the following audio file accurately."},
    #         {"role": "user", "content": file_path}
    #     ]
    # )
    # return completion.choices[0].message.content
    with open(file_path, "rb") as file:
        # Create a translation of the audio file
        translation = groq_client.audio.translations.create(
        file=(file_path, file.read()), # Required audio file
        model="whisper-large-v3", # Required model to use for translation
        prompt="Specify context or spelling",  # Optional
        response_format="json",  # Optional
        temperature=0.0  # Optional
        )
        # Print the translation text
        print(translation.text)
        return translation.text

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

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log Errors caused by Updates."""
    print(f"Update {update} caused error {context.error}")

# Initialize bot application
"""Create and configure the bot application."""
application = (
    Application.builder()
    .token(os.getenv("TELEGRAM_BOT_TOKEN"))
    .build()
)
# Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.VOICE, handle_voice))
application.add_error_handler(error_handler)

# async def main():
#     """Start the bot."""
#     application = await create_application()
#     print("Starting bot...")
    
#     # Add error handler
#     application.add_error_handler(error_handler)
    
#     print("Bot initialized successfully")
#     print("Bot started successfully")
#     await application.initialize()
#     try:
#         await application.start()
#         await application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
#     finally:
#         await application.stop()



if __name__ == '__main__':
    # asyncio.run(main())
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
