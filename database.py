import sqlalchemy
from sqlalchemy.ext import declarative
from sqlalchemy import orm

DATABASE_URL = f"sqlite:///main.db"

engine = sqlalchemy.create_engine(DATABASE_URL)

SessionLocal = orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative.declarative_base()
