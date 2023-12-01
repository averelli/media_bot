from dotenv import load_dotenv
import os

# load env variables from the .env file
load_dotenv()

# define the env vars
TELEGRAM_BOT_TOKEN = os.environ.get("BOT_TOKEN")