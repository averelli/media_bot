# media_bot
Telegram bot to update my database. Can be used to track tv shows, films and books. 

## Tracking books

1. Add a new book to the database using /book. Provide title; author; seriese after the command
2. Send a epub of that book to count words. No commnad needed, just the file
3. Insert data into the reading log table using command /blog. After the command provide a title and a reading status: s - started, c - continued, f - finished, b - binged in a day.
4. If the book is finished, use /book_end to rate the book and provide a comment.

## Tracking films

1. Using /film command to add a new row to the films log table. If this is the first time this film is added, provide film length along with other info. Input: title; language; length(for new films only).
2. To check if the film exists in the database, use /check command along with a film title.

## Tracking TV shows

Using /show command, pass the title of the show (lowercase); episode range start; episode range end; length of an episode; season number; language.
Episode range start should be the number of the episode in the season and the range end should be the last episode number that was watched that day. So if the user watched from episode number 3 to 5, these values should be passed. If only one episode was watched, pass the number of the episode in both values. 
Ex: watched episode 7 of The Crown, season 1 in English, episode was 60 min. Input: the crown; 7; 7; 60; 1; en

## Help command
Help command provides input examples while using the bot.

## Setup
Add an .env file containing a telegram bot token, then run settings.py file to import the token. 
Required packages for this project are in the requirements.txt