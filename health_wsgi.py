"""Temporary lightweight health WSGI app used only for deploy debugging.

This app intentionally doesn't import any heavy project modules (DB, models)
so it will always start quickly and respond on `/`, `/ping` and `/api`.
Deploy this briefly to verify Render is using the repository startCommand.
Remove or revert after debugging.
"""
from flask import Flask, jsonify

app = Flask(__name__)


@app.route('/', methods=['GET'])
def root():
    return jsonify({'status': 'health-ok'}), 200


@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'pong'}), 200


@app.route('/api', methods=['GET'])
def api():
    return jsonify({'api': 'health-ok'}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(__import__('os').environ.get('PORT', 5000)))
