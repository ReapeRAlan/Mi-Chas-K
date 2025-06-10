import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# Retrieve DATABASE_URL and strip any accidental whitespace.
raw_url = os.getenv("DATABASE_URL")

if raw_url:
    DATABASE_URL = raw_url.strip()
else:
    # Build from individual credentials, stripping whitespace from each piece.
    user = os.getenv("DB_USER", "").strip()
    password = os.getenv("DB_PASS", "").strip()
    host = os.getenv("DB_HOST", "").strip()
    port = os.getenv("DB_PORT", "").strip()
    name = os.getenv("DB_NAME", "").strip()
    DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{name}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
