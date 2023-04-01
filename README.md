# Parrot - learn English from books

Script helps you to learn english sentences from books you actually read. It shows you English sentence or word, and you have to write it in Polish.

Run pipenv to install necessary packages:

    pipenv sync

Run alembic migrations:

    alembic upgrade head

To get sentences list you have to:
* translate using https://translate.google.com/?sl=en&tl=pl&op=translate
* save translations
* export translations to docs.google.com
* import as csv separated by `;`
* load to db using `./load_translations.py file.csv`

Run script to practice:

    ./parrot.py
