from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import sqlalchemy as db

Base = declarative_base()

class Team(Base):
	__tablename__ = 'teams'

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(255), unique=True)
	enabled = db.Column(db.Boolean)

	def __init__(self, name, enabled=True):
		self.name = name
		self.enabled = enabled

class Service(Base):
	__tablename__ = 'services'

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(255), unique=True)
	group = db.Column(db.String(255))
	check = db.Column(db.String(255))
	enabled = db.Column(db.Boolean)

	def __init__(self, name, group, check, enabled=True):
		self.name = name
		self.check = check
		self.group = group
		self.enabled = enabled

class TeamService(Base):
	__tablename__ = 'team_service'

	id = db.Column(db.Integer, primary_key=True)
	
	team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
	team = relationship('Team')
	
	service_id = db.Column(db.Integer, db.ForeignKey('services.id'))
	service = relationship('Service')

	key = db.Column(db.String(255))
	value = db.Column(db.Text)
	edit = db.Column(db.Boolean)
	order = db.Column(db.Integer)

	def __init__(self, team, service, key, value, edit=True, order=0):
		self.team = team
		self.service = service
		self.key = key
		self.value = value
		self.edit = edit
		self.order = order

class Check(Base):
	__tablename__ = 'checks'

	id = db.Column(db.Integer, primary_key=True)

	team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
	team = relationship('Team')

	service_id = db.Column(db.Integer, db.ForeignKey('services.id'))
	service = relationship('Service')

	round = db.Column(db.Integer)
	time = db.Column(db.DateTime)
	passed = db.Column(db.Boolean)
	output = db.Column(db.Text)

	def __init__(self, team, service, round, passed, output):
		self.team_id = team
		self.service_id = service
		self.round = round
		self.passed = passed
		self.output = output
		self.time = datetime.utcnow()
