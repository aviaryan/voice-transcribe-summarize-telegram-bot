import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq
import tempfile
from dotenv import load_dotenv

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
        
        # Split and send transcription if it's too long
        if len(transcription) > 3000:  # Leave room for summary and formatting
            await status_message.edit_text("📝 *Transcription (Part 1):*", parse_mode='Markdown')
            
            # Split transcription into chunks of 4000 characters
            chunk_size = 4000
            transcription_chunks = [transcription[i:i + chunk_size] 
                                 for i in range(0, len(transcription), chunk_size)]
            
            # Send transcription chunks
            for i, chunk in enumerate(transcription_chunks, 1):
                await update.message.reply_text(
                    f"*Transcription (Part {i}):*\n{chunk}",
                    parse_mode='Markdown'
                )
            
            # Send summary separately
            await update.message.reply_text(
                "📌 *Summary:*\n"
                f"{summary}",
                parse_mode='Markdown'
            )
        else:
            # Send everything in one message if it's short enough
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
    with open(file_path, "rb") as file:
        translation = groq_client.audio.translations.create(
            file=(file_path, file.read()), # Required audio file
            model="whisper-large-v3", # Required model to use for translation
            prompt="Specify context or spelling",  # Optional
            response_format="json",  # Optional
            temperature=0.0  # Optional
        )
        return translation.text.strip()

async def generate_summary(text: str) -> str:
    """Generate a summary using LLama 3 via Groq API."""
    completion = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # Replace with actual Groq LLama 3 model name
        messages=[
            {"role": "system", "content": "Generate a concise summary of the following text:"},
            {"role": "user", "content": text}
        ],
        max_completion_tokens=32768,
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

if __name__ == '__main__':
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
