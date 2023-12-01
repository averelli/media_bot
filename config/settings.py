from dotenv import load_dotenv
import os

# load env variables from the .env file
load_dotenv()

# define the env vars
TELEGRAM_BOT_TOKEN = os.environ.get("BOT_TOKEN")
DB_NAME = os.environ.get("DB_NAME")
USER = os.environ.get("USER") 
PASSWORD = os.environ.get("PASSWORD")
HOST = os.environ.get("HOST")
PORT = os.environ.get("PORT")