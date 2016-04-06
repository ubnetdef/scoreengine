from config import config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Init SQLAlchemy
engine = create_engine(config['DATABASE_URI'])
SessionMaker = sessionmaker(bind=engine)
session = SessionMaker()
