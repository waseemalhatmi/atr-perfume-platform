#!/usr/bin/env python
"""
Enterprise Celery Worker Entry Point.
Run this using: celery -A celery_worker.celery_app worker --loglevel=info
"""

import os
from dotenv import load_dotenv

# Load environment variables before creating app
load_dotenv()

from app import create_app

# Create Flask app instance
app = create_app()

# Expose the Celery instance for the worker to find
celery_app = app.extensions.get("celery")

if __name__ == "__main__":
    celery_app.start()
