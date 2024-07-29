FROM python:3.10

WORKDIR /usr/src/app
COPY . /usr/src/app

RUN apt-get update && apt-get install -y ffmpeg && apt-get clean
RUN python3 -m venv venv
RUN . venv/bin/activate
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install gunicorn

RUN mkdir -p /usr/src/app/static/uploads

EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]