"""WSGI entrypoint for Gunicorn.

This file exposes a top-level `app` variable so servers (gunicorn) can import
it via `wsgi:app`. It simply imports the Flask `app` object from the package
`backend.app` to avoid package-relative import issues during WSGI startup.
"""
from backend.app import app  # noqa: E402


if __name__ == '__main__':
    # Allow local debugging with: python wsgi.py
    port = int(__import__('os').environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
