# Voice Note Transcription and Summarizer Bot for Telegram 🎙️📝

A powerful Telegram bot that transcribes and summarizes voice notes using state-of-the-art AI models. Built with Python and powered by Groq's API with Whisper and Llama 3 model for transcription and summarization.

## Screenshots 📸

| Transcription Example | Summary Example |
|:---:|:---:|
| <img width="611" alt="Image" src="https://github.com/user-attachments/assets/cc4adcbd-247b-496a-9359-15ed56a97e00" /> | <img width="624" alt="Image" src="https://github.com/user-attachments/assets/39a6f1ef-f6f6-4563-8ff9-4d3ee6fe4cbf" /> |

## Features ✨

- Transcribe voice notes from forwarded messages
- Handle direct voice note recordings
- Generate accurate transcriptions using Whisper
- Provide concise summaries of the transcribed content using Llama 3
- Support for multiple audio formats
- Well-formatted, easy-to-read output

## Prerequisites 📋

- Python 3.10 or higher
- pipenv (Python package manager)
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Groq API Key ([Get it here](https://console.groq.com))

## Installation 🚀

1. Clone the repository:
   ```bash
   git clone https://github.com/aviaryan/voice-transcribe-summarize-telegram-bot.git
   cd voice-transcribe-summarize-telegram-bot
   ```

2. Install dependencies using pipenv:
   ```bash
   pipenv install
   ```

3. Create a `.env` file in the root directory:
   ```bash
   cp .env.copy .env
   ```

4. Fill in your environment variables in the `.env` file:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   GROQ_API_KEY=your_groq_api_key
   ```

5. Configure authorized users:
   - Open `bot.py` and locate the `AUTHORIZED_USERS` array
   - Add your Telegram user ID to the array (you can get your ID by messaging @userinfobot on Telegram)
   ```python
   AUTHORIZED_USERS = [your_telegram_id]  # Add more user IDs as needed
   ```

## Usage 🎯

1. Activate the virtual environment:
   ```bash
   pipenv shell
   ```

2. Start the bot:
   ```bash
   python bot.py
   ```

3. In Telegram:
   - Forward any message containing a voice note to the bot
   - Record and send a voice note directly to the bot
   - Wait for the bot to process and return both transcription and summary

## How it Works 🔄

1. The bot receives a voice note through Telegram
2. Audio is processed and sent to Groq's API
3. Whisper model transcribes the audio content
4. Another pass through Groq's API generates a concise summary using Llama 3 model
5. Both transcription and summary are returned to the user in a well-formatted message

## Contributing 🤝

Contributions are welcome! Feel free to:
- Open issues for bugs or feature requests
- Submit pull requests
- Improve documentation
- Share feedback

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.
