# 🎧 Podcast Metadata

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

## 🏗️ Deployment

1. Install [docker](https://docs.docker.com/engine/install/) and [docker-compose](https://docs.docker.com/compose/install/linux/).

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

4. Create a new apache configuration in `/etc/apache2/sites-available/metadata.bilyk.gq.conf`.

   ```apacheconf
   <VirtualHost *:80>
       ServerAdmin admin@gauz.net
       ServerName metadata.bilyk.gq

       ProxyPreserveHost On
       ProxyPass / http://localhost:8000/
       ProxyPassReverse / http://localhost:8000/

       ErrorLog ${APACHE_LOG_DIR}/podcast_metadata_error.log
       CustomLog ${APACHE_LOG_DIR}/podcast_metadata_access.log combined
   </VirtualHost>
   ```

5. Enable the new configuration.

   ```bash
   a2ensite metadata.bilyk.gq.conf
   systemctl reload apache2
   ```

6. If the website is accessible on HTTP, create an SSL certificate and a new apache config
   using [certbot](https://certbot.eff.org/).

   ```bash
   certbot
   ```
