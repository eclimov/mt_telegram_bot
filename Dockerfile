FROM python:3.6-alpine

WORKDIR "/application"

COPY . /application
ENV PYTHONPATH "${PYTHONPATH}:/application"

#RUN pip3 install pipreqs
#RUN pipreqs .
#RUN pip3 install -r requirements.txt

#RUN pip3 install cffi --upgrade
#RUN apt-get update
#RUN apk update
RUN apk add -U --no-cache gcc build-base linux-headers ca-certificates python3-dev libffi-dev libressl-dev libxml2-dev libxslt-dev build-dep -y lxml \
    && pip install python-telegram-bot --upgrade \
    && pip install gspread \
    && pip install requests \
    && pip install bs4 \
    && pip install beautifulsoup4 \
    && pip install oauth2client


ENTRYPOINT python3 ./src/app.py
#CMD [ "python", "./application/myscript.py" ]