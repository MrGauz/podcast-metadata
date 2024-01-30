# Podcast Metadata

## Local Development

1. Pull [the repository](https://github.com/MrGauz/podcast-metadata) and `cd` into it.

    ```bash
    git pull git@github.com:MrGauz/podcast-metadata.git
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