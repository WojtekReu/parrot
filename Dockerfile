FROM python:3-bookworm

WORKDIR /app

COPY . /app

RUN set -eux; \
	apt-get update; \
	apt-get install -y --no-install-recommends \
		dictd \
        dict-freedict-eng-pol

COPY dictd.conf /etc/dictd/dictd.conf

RUN pip install pipenv

#RUN pipenv sync

#RUN pip install uvicorn fastapi
RUN LANG=C.UTF-8 LC_ALL=C.UTF-8 pipenv install --system --ignore-pipfile --deploy

RUN python3 install.py

RUN alembic upgrade head

# CMD ["fastapi", "run", "app/main.py", "--port", "80"]
 CMD ["python3","-m", "uvicorn", "api.server:app", "--port=8000", "--host=0.0.0.0"]
