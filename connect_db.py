import psycopg2
from config.settings import DB_NAME, USER, PASSWORD, HOST, PORT
from logs.logging_config import get_logger
from sqlalchemy import create_engine

# get a logger
logger = get_logger("DB_CONNECT")

def send_query(query, values = None):

    # get a connection 
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT
    )

    # a placeholder for a response
    response = None

    # get a cursor
    with conn.cursor() as curr:
        try:
            # check if there are values to pass into the query
            if values:
                curr.execute(query, values)
                try:
                    # if it was a select query, get response
                    response = curr.fetchall()
                except Exception as e:
                    logger.info("No results to fetch")
            else:
                curr.execute(query)
                response = curr.fetchall()
            
            # commit changes
            conn.commit()
            logger.info("Query executed successfully")
        except Exception as e:
            # if there was an error, rollback any changes
            logger.error(type(e).__name__)
            conn.rollback()
            raise Exception
            
    # close connection and return response
    conn.close()
    return response