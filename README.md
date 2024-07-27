# 🎧 Podcast Metadata

This is a Flask-powered website that allows you to embed podcast metadata like *Title*, *Track number*, etc. into an MP3
 or WAV file using a simple interface.
[Have a look at it here](https://metadata.bilyk.gq/) or run it yourself with the instructions below.

Full list of supported tags:

- TIT2 (Title)
- TPE1 (Author)
- TALB (Album)
- TYER (Year)
- TCON (Genre)
- TRCK (Track number)
- APIC (Cover art)
- CTOC & CHAP (Chapters)

## 👨‍💻 Local Development

1. Clone [the repository](https://github.com/MrGauz/podcast-metadata) and `cd` into it.

    ```bash
    git clone https://github.com/MrGauz/podcast-metadata.git
    cd podcast-metadata
    ```

2. Create a virtual environment and install dependencies.

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3. Run the application.

    ```bash
    python3 app.py --debug
    ```

   > ⚠️ Never run `--debug` in production.

## 🏗️ Initial Deployment

1. Install [docker](https://docs.docker.com/engine/install/)
   and [docker-compose](https://docs.docker.com/compose/install/linux/).

2. Clone [the repository](https://github.com/MrGauz/podcast-metadata) and `cd` into it.

    ```bash
    git clone https://github.com/MrGauz/podcast-metadata.git
    cd podcast-metadata
    touch db.sqlite
    ```

3. Start the container.

    ```bash
    docker-compose up -d
    ```

4. Create a new nginx 
   [configuration in `/etc/nginx/sites-available/metadata.bilyk.gq`](./etc/nginx/sites-available/metadata.bilyk.gq).

5. Enable the new configuration.

   ```bash
   ln -s /etc/nginx/sites-available/metadata.bilyk.gq /etc/nginx/sites-enabled/
   systemctl reload nginx
   ```

6. Create an SSL certificate and a new apache config using [certbot](https://certbot.eff.org/).

   ```bash
   certbot
   ```

## 🚀 Update

1. Pull the latest changes.

    ```bash
    git pull
    ```

2. Restart the container.

    ```bash
    docker compose down
    docker compose up -d --build
    docker system prune --all --volumes --force
    ```
