# Podcast Metadata

## Local Development

1. Pull [the repository]() and `cd` into it.
```bash
git pull TODO
cd TODO
```

2. Create a virtual environment and install dependencies.
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Create a `.env` file (see `.env.example` for reference).
```bash
cp .env.example .env
```

4. Run the application.
```bash
flask run
```