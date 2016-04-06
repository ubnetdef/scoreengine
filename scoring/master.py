from scoring import Session
from scoring.models import Team, Service, TeamService, Check
from datetime import datetime
from time import sleep
from thread import start_new_thread, allocate_lock
import random
import importlib

"""
ScoringEngine

Responsible for creating new CheckRound objects
at specific intervals
"""
class Master(object):
	def __init__(self):
		self.started = datetime.utcnow()
		self.round = 0

		self.printLock = allocate_lock()
		self.session = Session()

	def run(self):
		while True:
			self.round += 1
			start_new_thread(self.new_round, ())

			sleep(60)

	def new_round(self):
		# Make a new session for this thread
		session = Session()

		# Get all the active teams for this round
		teams = []
		for team in session.query(Team).filter(Team.enabled == True):
			teams.append({
				'id': team.id,
				'name': team.name
			})

		# Get all active services for this round
		services = []
		for service in session.query(Service).filter(Service.enabled == True):
			services.append({
				'id': service.id,
				'name': service.name,
				'group': service.group,
				'check': service.check
			})

		# Close the session
		session.close()

		# Start the checks!
		for team in teams:
			for service in services:
				start_new_thread(self.new_check, (team, service))

	def new_check(self, team, service, dryRun=False):
		check = ServiceCheck(team, service, Session())

		check.run()

		if dryRun:
			self.printLock.acquire()
			print "---------[ TEAM: %s | SERVICE: %s" % (team["name"], service["name"])
			for line in check.getOutput():
				print line
			print "---------[ PASSED: %r" % (check.getPassed())
			self.printLock.release()
		else:
			session = Session()
			session.add(Check(team["id"], service["id"], check.getPassed(), "\n".join(check.getOutput())))
			session.commit()
			session.close()

			# Print out some data
			self.printLock.acquire()
			print "Round: %04d | %s | Service: %s | Passed: %r" % (self.round, team["name"].ljust(8), service["name"].ljust(10), check.getPassed())
			self.printLock.release()

class ServiceCheck(object):
	def __init__(self, team, service, session):
		self.team = team
		self.service = service
		self.session = session

		self.passed = False
		self.output = []

	def run(self):
		# Get all the service data for this check
		checkDataDB = self.session.query(TeamService)\
					.filter(TeamService.team_id == self.team["id"])\
					.filter(TeamService.service_id == self.service["id"])\
					.order_by(TeamService.order)

		checkDataInitial = {}
		
		for data in checkDataDB:
			if data.key not in checkDataInitial:
				checkDataInitial[data.key] = []

			checkDataInitial[data.key].append(data.value)

		checkData = {}
		for key, value in checkDataInitial.iteritems():
			if len(value) == 1:
				checkData[key] = value[0]
			else:
				checkData[key] = random.choice(checkDataInitial[key])

		# Special handling of "USERPASS"
		if "USERPASS" in checkData:
			(checkData["USER"], checkData["PASS"]) = checkData["USERPASS"].split("||")

			del checkData["USERPASS"]

		# Call it!
		self.getCheck()(self, checkData)

		# Close the session
		self.session.close()

	def getCheck(self):
		group = importlib.import_module('scoring.checks.%s' % (self.service["group"]))

		return getattr(group, self.service["check"])

	def addOutput(self, message):
		self.output.append(message)

	def getOutput(self):
		return self.output

	def setPassed(self):
		self.passed = True

	def getPassed(self):
		return self.passed

	def getTeamName(self):
		return self.team["name"]

	def getServiceName(self):
		return self.service["name"]