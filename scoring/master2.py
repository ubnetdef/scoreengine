from __future__ import print_function
from datetime import datetime
from scoring import celery_app, Session
from scoring.models import Team, Service, TeamService, Check
import config
import random
import importlib
import time
import threading

class Master(object):
	def __init__(self, round=0):
		self.started = datetime.utcnow()
		self.round = round
		self.tasks = []
		self.reaper = None

		self.sleep_startrange = (config.ROUND["time"]-config.ROUND["jitter"])
		self.sleep_endrange = (config.ROUND["time"]+config.ROUND["jitter"]+1)

	def run(self):
		# Launch the reaper thread
		self.reaper = threading.Thread(target=self.start_reaper)
		self.reaper.start()

		# Launch the round handler
		self.start_rounds()

	def start_rounds(self):
		while True:
			self.round += 1

			# Start our round thread
			round_thread = threading.Thread(target=self.start_round, args=(self.round,))
			round_thread.start()

			# Go to sleep
			time.sleep(random.randrange(self.sleep_startrange, self.sleep_endrange))

	def start_reaper(self):
		while True:
			# Iterate over the tasks, check for any that are completed
			for t in self.tasks:
				task = self.check_task.AsyncResult(t)
				
				if task.state == "PENDING":
					continue

				print("REAPER: Reaping {}".format(t))
				session = Session()

				chk = Check(task.result['team_id'],
						task.result['service_id'],
						task.result['round'],
						task.result['passed'],
						"\n".join(task.result['output']))

				session.add(chk)
				session.commit()

				session.close()

				task.forget()
				self.tasks.remove(t)

			time.sleep(15)

	def start_round(self, round):
		# Grab all the Team Services that are (currently) enabled
		session = Session()
		teams = [t.id for t in session.query(Team).filter(Team.enabled == True).all()]
		services = session.query(Service).filter(Service.enabled == True).all()
		teamservices = []

		for team in teams:
			for service in services:
				check = {
					"name": service.name,
					"group": service.group,
					"func": service.check,
				}
				teamservices.append(self.buildServiceCheck(session, round, team, service.id, check))

		session.close()

		# Shuffle it up
		random.shuffle(teamservices)

		# Create the tasks
		for sc in teamservices:
			task = self.check_task.delay(sc)
			self.tasks.append(task.id)

			print("Created Task #{}".format(task.id))

	def buildServiceCheck(self, session, round, team, service, check):
		data = session.query(TeamService) \
			.filter(TeamService.team_id == team, TeamService.service_id == service) \
			.all()

		checkDataInitial = {}
		for d in data:
			if d.key not in checkDataInitial:
				checkDataInitial[d.key] = []
			checkDataInitial[d.key].append(d.value)

		checkData = {}
		for key, value in checkDataInitial.iteritems():
			checkData[key] = random.choice(checkDataInitial[key])

		# Special handling of "USERPASS"
		if "USERPASS" in checkData:
			(checkData["USER"], checkData["PASS"]) = checkData["USERPASS"].split("||")

			del checkData["USERPASS"]

		return {
			"team_id": team,
			"service_id": service,
			"round": round,
			"config": checkData,
			"check": check,
			"passed": False,
			"output": [],
		}

	@staticmethod
	@celery_app.task
	def check_task(sc):
		# Load the check class
		group = importlib.import_module('scoring.checks.{}'.format(sc["check"]["group"]))
		check = getattr(group, sc["check"]["func"])

		service = ServiceConfig(sc)
		check(service, service.getConfig())

		return service.export()

class ServiceConfig(object):
	def __init__(self, sc):
		self.service = sc

	def getConfig(self):
		return self.service["config"]

	def getServiceName(self):
		return self.service["check"]["name"]

	def setPassed(self):
		self.service["passed"] = True

	def addOutput(self, message):
		self.service["output"].append(message)

	def export(self):
		return self.service