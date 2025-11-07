"""WSGI entrypoint for Gunicorn.

This file exposes a top-level `app` variable so servers (gunicorn) can import
it via `wsgi:app`. It simply imports the Flask `app` object from the package
`backend.app` to avoid package-relative import issues during WSGI startup.
"""
try:
    # Import the real app. If this raises, we'll catch and try a secondary
    # module (`backend.app_fixed`) which contains a cleaned copy used for
    # local recovery. If both fail we fall back to a minimal app so the
    # process stays alive and the full traceback appears in the service logs.
    from backend.app import app  # noqa: E402
except Exception:
    # Print traceback to stdout so Render logs capture the error.
    import traceback
    traceback.print_exc()

    # If the original import failed (syntax error in backend.app), try the
    # cleaned backup module created by the helper script.
    try:
        from backend.app_fixed import app as app  # noqa: E402
    except Exception:
        # If that also fails, expose a minimal Flask app so Gunicorn can bind
        # and we can inspect logs to debug the issue.
        import traceback as _tb
        _tb.print_exc()
        from flask import Flask, jsonify

        app = Flask(__name__)

        @app.route('/')
        def fallback_root():
            return jsonify({
                'status': 'error',
                'message': 'backend import failed; check logs for traceback'
            }), 500


if __name__ == '__main__':
    # Allow local debugging with: python wsgi.py
    port = int(__import__('os').environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
