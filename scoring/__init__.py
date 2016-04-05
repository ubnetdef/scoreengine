from config import config
from sqlalchemy import create_engine

# Init SQLAlchemy
db = create_engine(config['DATABASE_URI'])
