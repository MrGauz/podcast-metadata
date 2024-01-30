FROM python:3.10

WORKDIR /usr/src/app
COPY . /usr/src/app

RUN python3 -m venv venv
RUN . venv/bin/activate
RUN pip3 install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["python3", "app.py"]
