from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import config

# Init Celery
celery_app = Celery("scoreengine", backend=config.CELERY["BACKEND"], broker=config.CELERY["BROKER"])

# Init SQLAlchemy
engine = create_engine(config.DATABASE_URI, **config.DATABASE_EXTRA)
SessionMaker = sessionmaker(bind=engine)
Session = scoped_session(SessionMaker)
