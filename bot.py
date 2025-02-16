import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq
import tempfile
from dotenv import load_dotenv
import asyncio
from collections import defaultdict
from time import time
load_dotenv()

# List of authorized user IDs
AUTHORIZED_USERS = [95165304]  # Add more user IDs as needed

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Message buffer to store messages per user
message_buffers = defaultdict(list)
# Store the task references to cancel them if needed
buffer_tasks = {}
# Buffer timeout in seconds
BUFFER_TIMEOUT = 0.5

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
        # Check user authorization
        if update.effective_user.id not in AUTHORIZED_USERS:
            await update.message.reply_text("⛔ Sorry, you are not authorized to use this bot. Contact @aviaryan.")
            return

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
        transcription = groq_client.audio.transcriptions.create(
            file=(file_path, file.read()), # Required audio file
            model="distil-whisper-large-v3-en", # Required model to use for transcription
            # ^ using cheapest model to manage costs (https://groq.com/pricing/)
            # prompt="Specify context or spelling",  # Optional
            # response_format="json",  # Optional
            # temperature=0.0  # Optional
        )
        return transcription.text.strip()

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

async def process_buffered_messages(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Process all buffered messages for a user after the timeout."""
    try:
        await asyncio.sleep(BUFFER_TIMEOUT)
        
        # Get all messages from the buffer
        messages = message_buffers[user_id]
        if not messages:
            return
            
        # Get the chat_id and original message for reply
        chat_id = messages[0]['chat_id']
        original_message = messages[0]['message']
        
        # Combine all message texts
        combined_text = "\n".join(msg['text'] for msg in messages)
        
        # Clear the buffer for this user
        message_buffers[user_id].clear()
        
        # Send processing status
        status_message = await context.bot.send_message(
            chat_id=chat_id,
            text="📝 Generating summary..."
        )
        
        # Generate summary
        summary = await generate_summary(combined_text)
        
        # Send the summary
        await status_message.edit_text(
            "📌 *Summary:*\n"
            f"{summary}",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        if messages and messages[0]['chat_id']:
            await context.bot.send_message(
                chat_id=messages[0]['chat_id'],
                text=f"❌ Sorry, an error occurred: {str(e)}"
            )
    finally:
        # Clean up
        if user_id in buffer_tasks:
            del buffer_tasks[user_id]

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages and buffer them for combined summary."""
    try:
        user_id = update.effective_user.id
        
        # Check user authorization
        if user_id not in AUTHORIZED_USERS:
            await update.message.reply_text("⛔ Sorry, you are not authorized to use this bot. Contact @aviaryan.")
            return
        
        # Store message info
        message_info = {
            'text': update.message.text,
            'chat_id': update.effective_chat.id,
            'message': update.message,
            'timestamp': time()
        }
        message_buffers[user_id].append(message_info)
        
        # Cancel existing task if any
        if user_id in buffer_tasks and not buffer_tasks[user_id].done():
            buffer_tasks[user_id].cancel()
        
        # Create new task to process messages after timeout
        buffer_tasks[user_id] = asyncio.create_task(
            process_buffered_messages(user_id, context)
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Sorry, an error occurred: {str(e)}")

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
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))  # Add text message handler
application.add_error_handler(error_handler)

if __name__ == '__main__':
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
