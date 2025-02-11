# Voice Note Summarizer Bot for Telegram

This is a telegram bot that can be hosted on a serverless setup. The code is created in python.

This bot accepts message forwards that contain voice notes in telegram. As well as you can record your own voice and send that voice note to the bot.

Once the bot receives a telegram message with a voice note attached it transcribes it using Groq's api with the latest llama 3 model. Then it feeds it to whisper again using Groq api.
Eventually the bot returns both the transcription in a well formatted format, as well as the summary of the transcript.

We use pipenv to manage python dependencies.
