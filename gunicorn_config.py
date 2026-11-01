"""Gunicorn configuration for Render / cloud deployment."""
import os

bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
workers = 1          # Free tier: keep to 1 worker to stay within 512 MB RAM
threads = 2
timeout = 120
preload_app = True
