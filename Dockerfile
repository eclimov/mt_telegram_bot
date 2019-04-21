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

# lxml may "eat" of of the RAM during installing, - this my be fixed by adding ~1G swap file to the system (command for check: `free -h`)
RUN apk add -U --no-cache gcc build-base linux-headers ca-certificates python3-dev libffi-dev libressl-dev libxslt-dev \
    && pip install python-telegram-bot --upgrade \
    && pip install gspread \
    && pip install lxml \
    && pip install requests \
    && pip install bs4 \
    && pip install beautifulsoup4 \
    && pip install oauth2client


ENTRYPOINT python3 ./src/app.py
#CMD [ "python", "./application/myscript.py" ]