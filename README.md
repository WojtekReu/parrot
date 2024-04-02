# Parrot - learn English from books

This project helps you learn new words from the book you are reading. It uses the flashcard 
technique to increase memorization process. All you need is your book in text format, and
list of translated phrases. You can download book from https://www.gutenberg.org/ or 
https://archive.org/

Run pipenv to install necessary packages:

    pipenv sync

Run alembic migrations:

    alembic upgrade head

Add author and title to database. You can import it from prepared file data/book_list.csv 
separated by tabs (see book_list.example.csv):

    ./import_books.py

You can download book in txt format 
https://archive.org/stream/TheOldManAndTheSea-Eng-Ernest/oldmansea_djvu.txt
and load to database:

    ./load_book_content.py Ernest_Hemingway/The_Old_man_and_the_Sea.txt

Load your translations to database:

    ./load_translations.py translations/Ernest_Hemingway/The_Old_man_and_the_Sea.csv


The best way to prepare sentences list is using google translator and "saved":
* translate using https://translate.google.com/?sl=en&tl=pl&op=translate
* save translations
* export translations to docs.google.com
* import as csv separated by `;`
* load to db using script
 `./load_translations.py translations/Ernest_Hemingway/The_Old_man_and_the_Sea.csv`

Run FastAPI service:

    python -m uvicorn api.server:app --reload

Run client based on Vue.js:

    cd client
    npm run serve
