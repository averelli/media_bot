from config.settings import TELEGRAM_BOT_TOKEN
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters, MessageHandler
from connect_db import send_query
from logs.logging_config import get_logger
from ebooklib import epub
from bs4 import BeautifulSoup
import logging
import ebooklib
import os

def get_date():
    # Get the current date and time
    now = datetime.now()

    # If the current time is between 00:00 and 01:00, consider it as the previous day
    if now.hour < 1:
        previous_day = now - timedelta(days=1)
    else:
        previous_day = now

    # Extract the date part
    return previous_day.date()

def count_words_in_epub(path):
    book = epub.read_epub(path)
    word_count = 0
    for item in book.items:
        if isinstance(item, ebooklib.epub.EpubHtml):
            # Extract and clean text from the document using BeautifulSoup
            content = item.get_body_content()
            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text()
            words = text.split()
            word_count += len(words)
    word_count -= 1000
    return word_count

async def book_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Got a request to update the book log")

    try:
        # unpack input
        info_joined = " ".join(context.args)
        info = [x.strip() for x in info_joined.split(";")]

        # get title
        title = info[0]

        # get the date
        date = get_date()

        # get the status 
        status = "binged" if info[1] == "b" else "started" if info[1] == "s" else "continued" if info[1] == "c" else "finished"
        
        # get percent read
        percent_read = int(info[1]) 
        
        # calculate percent delta to insert
        if status == "continued" or status == "finished":
            logger.info("Sent query to calculate the percentage delta")
            total_percent = send_query("SELECT SUM(percentage) OVER (PARTITION BY book_id ORDER BY date) FROM reading.books_log ORDER BY date desc LIMIT 1;")[0][0]
            insert_percent = percent_read - int(total_percent)
        else:
            insert_percent = percent_read

        # get the book id
        book_id = send_query("SELECT book_id FROM reading.book WHERE title = %s;",(title,))[0][0]
        logger.info("Got the book_id")

        # insert values into the log
        send_query(
            "INSERT INTO reading.books_log (date, book_id, status, percentage) VALUES (%s, %s, %s, %s)",
            (date, book_id, status, insert_percent)
        )
        logger.info("Inserted into the book log")
        
        await update.message.reply_text("Updated the book_log successfully!")

        #check if finished
        if status == "finished" or status == "binged":
            # save the book id for later use
            context.user_data["book_id"] = book_id
            await update.message.reply_text("Now please use the /book_end command to rate and add comments")
        
    except Exception as e:
        logger.error(type(e).__name__)
        await update.message.reply_text("Something went wrong. Try again")

async def book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Got a request to add a new book")

    try:
        # unpack input
        info_joined = " ".join(context.args)
        info = [x.strip() for x in info_joined.split(";")]

        title = info[0]
        author = info[1]
        series = None if info[2] == "none" else info[2]

        # insert values
        logger.info("Sent data into db")
        send_query("INSERT INTO reading.book (title, author, series) VALUES (%s, %s, %s);",(title, author, series))
        
        # log
        logger.info("Data inserted into reading.book")  

        context.user_data["book_id"] = send_query("SELECT MAX(book_id) FROM reading.book")[0][0]
        await update.message.reply_text(f"Now please send the epub file to count words")
    
    except Exception as e:
        logger.error(type(e).__name__)
        await update.message.reply_text("Something went wrong. Try again")

async def count_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Got a request to count words in epub")
    try:
        # get epub
        epub = await update.message.document.get_file()

        # save epub to file
        await epub.download_to_drive("book.epub")

        # count the words
        words = count_words_in_epub("book.epub")
        logger.info("Words counted successfully")

        # delete the file
        os.remove("book.epub")

        # get the book_id
        book_id = context.user_data["book_id"]
        logger.info("Got book_id from db")

        # update reading.book table
        send_query("UPDATE reading.book SET word_count = %s WHERE book_id = %s", (words, book_id))
        logger.info("Updated the word count in the book table")

        await update.message.reply_text("Don't forget to update the reading log")
    
    except Exception as e:
        logger.error(type(e).__name__)
        await update.message.reply_text("Something went wrong. Try again")

async def book_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Got a finish book request")
    try:
        # unpack input
        info_joined = " ".join(context.args)
        info = [x.strip() for x in info_joined.split(";")]

        rating = info[0]
        comment = info[1]

        # get the book id
        book_id = context.user_data["book_id"]

        # update the reading.book table
        send_query("UPDATE reading.book SET rating = %s, comment = %s WHERE book_id = %s", (rating, comment, book_id))
        logger.info("Book table updated successfully")

        await update.message.reply_text("Book table updated successfully")

    except Exception as e:
        logger.error(type(e).__name__)
        await update.message.reply_text("Something went wrong. Try again")

async def check_film(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Got a check film request")
    try:
        # unpack input
        info_joined = " ".join(context.args)
        info = [x.strip() for x in info_joined.split(";")]

        # get title and lang
        title = info[0]

        # check if film exists
        check = send_query("SELECT * FROM films.film WHERE title = %s;",(title,))

        if check == []:
            await update.message.reply_text("This film is not in the database")
        else:
            await update.message.reply_text(f"Yes, this movie exists in the database\n {check[0]}")
    
    except Exception as e:
        logger.error(type(e).__name__)
        await update.message.reply_text("Something went wrong. Try again")

async def film(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Got a film request")
    try:
        # get date
        date = get_date()

        # unpack input
        info_joined = " ".join(context.args)
        info = [x.strip() for x in info_joined.split(";")]

        # get title and lang
        title = info[0]
        lang = info[1]

        # create a var to store film_id
        film_id = None

        # check if movie is new
        check = send_query("SELECT film_id FROM films.film WHERE title = %s;",(title,))
        logger.info("Checked if this film already exists")
        if check == []:
            logger.info("New film, inseting values into films.film")
            # this is a new film so the length must be provided
            length = info[2]

            # insert values into the film table
            send_query("INSERT INTO films.film (title, length) VALUES (%s, %s);",(title, length))
            logger.info("Inserted values into the film table")
            
            # get the new film_id
            film_id = send_query("SELECT film_id FROM films.film WHERE title = %s;",(title,))[0][0]
            logger.info("Got the new film_id")

        else:
            logger.info("Film is already in the table, got the film_id")
            film_id = check[0][0]

        # isert a row into films_log
        send_query("INSERT INTO films.films_log (date, film_id, language) VALUES (%s, %s, %s);", (date, film_id, lang))
        logger.info("Films log updated")

        update.message.reply_text("Film info processed successfully!")
    
    except Exception as e:
        logger.error(type(e).__name__)
        await update.message.reply_text("Something went wrong. Try again")

async def show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Got a show request")
    try:
        #get date
        date = get_date()

        # unpack input
        info_joined = " ".join(context.args)
        info = [x.strip() for x in info_joined.split(";")]    

        title = info[0]
        range_start = int(info[1])
        range_end = int(info[2])
        length = info[3]
        season = info[4]
        language = info[5]
        show_id = None

        # calculate how many episodes were watched
        num_watched = range_end - range_start + 1

        # check if a show exists and if yes, get id 
        check = send_query("SELECT show_id FROM shows.show WHERE title = %s;",(title,))
        if check == []:
            logger.info("This is a new show")

            # insert a new row into the show table
            send_query("INSERT INTO shows.show (title) VALUES (%s)",(title,))

            # get the new id
            show_id = send_query("SELECT show_id FROM shows.show WHERE title = %s;",(title,))[0][0]
        else:
            logger.info("This show already exists")
            show_id = check[0][0]

        # insert new rows
        logger.info(f"Start processing {num_watched} episodes")
        for episode in range(range_start, range_end +1):
            # check if this episode exists in the episode table
            check = send_query("SELECT episode_id FROM shows.episode WHERE show_id = %s and season = %s and episode_num = %s", (show_id, season, episode))

            if check == []:
                logger.info("This episode doesn't already exists, going to insert it")
                # episode doesn't yet exist, must be inserted
                send_query("INSERT INTO shows.episode (show_id, season, episode_num, length) VALUES (%s, %s, %s, %s)", (show_id, season, episode, length))

                # get the new episode's id
                ep_id = send_query("SELECT episode_id FROM shows.episode WHERE show_id = %s and season = %s and episode_num = %s", (show_id, season, episode))[0][0]
            else:
                logger.info("This episode already exists")
                ep_id = check[0][0]

            # isert a row with the episode into shows_log
            send_query("INSERT INTO shows.shows_log (date, episode_id, language) VALUES (%s, %s, %s)", (date, ep_id, language))
            logger.info("Inserted a row into shows_log")
    except Exception as e:
        logger.error(type(e).__name__)
        await update.message.reply_text(f"Something went wrong. Try again. Error: {type(e).__name__}")

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
            List of commands and their input formats:
            /book - add a new book then send epub file
            Input: title; author; series(pass none if none)
            /blog - add a books_log entry
            Input: title; status; percent read (total)
            /book_end - to rate and comment finished book
            Input: rating; comment
            /film - add film info or update log
            Input: title; language; length(only for new films)
            /check - check if a film is aready in the database
            Input: title
            /show - process show data after watching some episodes
            Input: title; episode_number_start; episode_number_end; length; season; language
""")

if __name__ == "__main__":
    # set higher logging level for httpx to avoid all GET and POST requests being logged
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram.ext.Application").setLevel(logging.WARNING)
    
    # create a logger instance
    logger = get_logger("BOT")
    
    # create a bot instance
    bot = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    logger.info("BOT STARTED")

    # handler to process films
    film_handler = CommandHandler("film", film)

    # handler to check if a film exists
    check_film_handler = CommandHandler("check", check_film)

    # handle epub 
    words_handler = MessageHandler(filters.ATTACHMENT, count_words)

    # book handler
    book_handler = CommandHandler("book", book)

    #handler to update book_log
    book_log_handler = CommandHandler("blog",book_log)

    # handle book rating and comment
    end_book_handler = CommandHandler("book_end", book_end)

    # handle shows input
    shows_handler = CommandHandler("show", show)

    # help handler
    help_handler = CommandHandler("help",help)

    bot.add_handler(book_log_handler)
    bot.add_handler(words_handler)
    bot.add_handler(book_handler)
    bot.add_handler(end_book_handler)
    bot.add_handler(film_handler)
    bot.add_handler(check_film_handler)
    bot.add_handler(help_handler)
    bot.add_handler(shows_handler)

    bot.run_polling()