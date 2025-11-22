FROM python:3.12-bookworm

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

COPY ./install.py /app
COPY ./.env /app

RUN /usr/bin/env python3 install.py

COPY . /app

CMD ["./entrypoint-web.sh"]
