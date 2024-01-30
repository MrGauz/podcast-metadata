FROM python:3.10

WORKDIR /usr/src/app
COPY . /usr/src/app

RUN python3 -m venv venv
RUN . venv/bin/activate
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install gunicorn

RUN touch db.sqlite
RUN mkdir -p /usr/src/app/static/uploads

EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]