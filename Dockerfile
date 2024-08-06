FROM python:3-bookworm

WORKDIR /app

RUN set -eux; \
	apt-get update; \
	apt-get install -y --no-install-recommends \
		dictd \
        dict-freedict-eng-pol; \
    apt-get clean;

COPY dictd.conf /etc/dictd/dictd.conf

RUN pip install --no-cache-dir pipenv

COPY ./Pipfile /app
COPY ./Pipfile.lock /app

RUN pipenv sync --system --clear

COPY ./docker.env /app
COPY ./install.py /app

RUN /usr/bin/env python3 install.py

COPY . /app

CMD ["python3", "-m", "uvicorn", "api.server:app", "--port=8000", "--host=0.0.0.0"]
