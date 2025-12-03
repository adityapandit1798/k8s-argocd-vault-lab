import os

# Load secrets from Vault if available
secrets_file = '/vault/secrets/flask.txt'
if os.path.exists(secrets_file):
    with open(secrets_file) as f:
        for line in f:
            if line.startswith('export '):
                key, val = line.replace('export ', '').strip().split('=', 1)
                os.environ[key] = val.strip('"')

from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return f"Hello from Flask! Environment: {os.getenv('ENV', 'dev')} | DB: {os.getenv('DB_PASSWORD', 'not set')}"

@app.route('/health')
def health():
    return {"status": "ok"}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
