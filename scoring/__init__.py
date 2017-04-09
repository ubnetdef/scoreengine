import config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session


# Init SQLAlchemy
engine = create_engine(config.DATABASE_URI, **config.DATABASE_EXTRA)
SessionMaker = sessionmaker(bind=engine)
Session = scoped_session(SessionMaker)
