import config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session


# Init SQLAlchemy
engine = create_engine(config.DATABASE_URI, pool_size=40, max_overflow=60)
SessionMaker = sessionmaker(bind=engine)
Session = scoped_session(SessionMaker)
