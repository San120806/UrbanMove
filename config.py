import os

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'urbanmove_secret_key_123')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')

    # MySQL database settings
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'urbanmove_pass')
    DB_NAME = os.environ.get('DB_NAME', 'urbanmove_db')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
