import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "gourmetdash-dev-secret")
    MONGO_URI  = os.getenv("MONGO_URI",  "mongodb://localhost:27017/gourmetdash")
    BCRYPT_LOG_ROUNDS = 12