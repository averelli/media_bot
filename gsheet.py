import gspread
from logs.logging_config import get_logger
from config.settings import GS_FILE

logger = get_logger("G_SHEETS_CONNECT")

# take the type of media: book, show, film
def update_db_from_sheets(m_type: str):
    try:
        # get credentials
        credentials = gspread.service_account()

        # open the needed spreadsheet
        spreadsheet = credentials.open(GS_FILE)
        
        # open the needed worksheet 
        table = spreadsheet.worksheet(m_type)
        logger.info("Connected to the worksheet")

    except Exception as e:
        logger.error("Wasn't able to connect to the spreadsheet")