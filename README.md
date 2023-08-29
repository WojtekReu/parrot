# Parrot - learn English from books

Script helps you to learn english sentences from books you actually read. It shows you English sentence or word, and you have to write it in Polish.

Run pipenv to install necessary packages:

    pipenv sync

Run alembic migrations:

    alembic upgrade head

Add author and title to database. You can import it from prepared file data/book_list.csv 
separated by tabs (see book_list.example.csv):

    ./import_books.py

If you have book in txt format, you can load it content to database:

    ./load_book_content.py Ernest_Hemingway/The_Old_man_and_the_Sea.txt

Load your translations to database:

    ./load_translations.py translations_file.csv

Run connect_words.py to link translations to sentences where your chosen word occurs.

    ./connect_words.py

The best way to prepare sentences list is using google translator and "saved":
* translate using https://translate.google.com/?sl=en&tl=pl&op=translate
* save translations
* export translations to docs.google.com
* import as csv separated by `;`
* load to db using script `./load_translations.py file.csv`

Run script to practice new words:

    ./parrot.py
