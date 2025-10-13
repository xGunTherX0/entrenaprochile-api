"""Temporary debug WWSGI app for deploy verification.

Use this by setting Render Start Command to:
  gunicorn debug_wsgi:app --bind 0.0.0.0:$PORT

Only intended for short-term debugging to confirm the service can start and
serve a simple route without importing the full backend stack.
"""
from flask import Flask, jsonify

app = Flask(__name__)


@app.route('/', methods=['GET'])
def root():
    return jsonify({'debug': 'ok', 'msg': 'debug_wsgi responding'}), 200


@app.route('/api', methods=['GET'])
def api_root():
    return jsonify({'api': 'debug-ok'}), 200


@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'pong'}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(__import__('os').environ.get('PORT', 5000)))
