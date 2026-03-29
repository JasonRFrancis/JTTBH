"""
JTTBH Development Entry Point
==============================
Run this file directly to start the Flask development server:

    python app/main.py

For production use Gunicorn:

    gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
"""

import sys
import os

# Ensure the project root (parent of this file's directory) is on sys.path so
# that `from app import create_app` resolves correctly regardless of cwd.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
