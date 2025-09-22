from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST=os.environ.get("DB_HOST")
DB_PORT=os.environ.get("DB_PORT")
DB_NAME=os.environ.get("DB_NAME")
DB_USER=os.environ.get("DB_USER")
DB_PASS=os.environ.get("DB_PASS")
SALT_BEELINE_TEST=os.environ.get("SALT_BEELINE_TEST")
SALT_BEELINE_PROD=os.environ.get("SALT_BEELINE_PROD")
SALT_BUBBLES=os.environ.get("SALT_BUBBLES")
SECRET_FOR_BEELINE=os.environ.get("SECRET_FOR_BEELINE")