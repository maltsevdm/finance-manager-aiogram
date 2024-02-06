from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.config import DB, PORT, HOST, PASS, USER

SQLALCHEMY_DATABASE_URL = f'postgresql://{USER}:{PASS}@{HOST}:{PORT}/{DB}'

engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

