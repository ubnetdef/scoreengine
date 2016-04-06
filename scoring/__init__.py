from config import config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# Init SQLAlchemy
engine = create_engine(config['DATABASE_URI'])
SessionMaker = sessionmaker(bind=engine)
Session = scoped_session(SessionMaker)