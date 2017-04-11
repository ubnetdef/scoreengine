from __future__ import print_function
from datetime import datetime
import config
import random
import scoring
import scoring.models as models
import scoring.worker
import signal
import sys
import time
import threading

class Master(object):
	def __init__(self, round=0):
		self.started = datetime.utcnow()
		self.round = round
		self.tasks = []
		self.round_tasks = {}
		self.reaper = None
		self.manager = None

		self.no_more_rounds = False

		self.sleep_startrange = (config.ROUND["time"]-config.ROUND["jitter"])
		self.sleep_endrange = (config.ROUND["time"]+config.ROUND["jitter"]+1)

		# Catch CTRL+C signal
		signal.signal(signal.SIGINT, self.shutdown)

	def shutdown(self, signal, frame):
		print("[MASTER] Caught CTRL+C. Shutting down rounds...")

		self.no_more_rounds = True
		print("{} tasks remaining. Waiting for them to finish before shutting down.".format(len(self.tasks)))

	def run(self):
		# Launch the reaper thread
		self.reaper = threading.Thread(target=self.start_reaper)
		self.reaper.start()

		# Launch the round handler
		self.start_rounds()

	def start_rounds(self):
		while not self.no_more_rounds:
			self.round += 1

			# Start our round thread
			round_thread = threading.Thread(target=self.start_round, args=(self.round,))
			round_thread.start()

			# Go to sleep
			time.sleep(random.randrange(self.sleep_startrange, self.sleep_endrange))

	def start_reaper(self):
		while not self.no_more_rounds or len(self.tasks) > 0:
			# Iterate over the tasks, check for any that are completed
			for t in self.tasks:
				task = scoring.worker.check_task.AsyncResult(t)
				
				if task.state == "PENDING":
					continue

				print("[REAPER] Reaping {}".format(t))
				session = scoring.Session()

				# Add the successful check
				chk = models.Check(task.result["team_id"],
						task.result["service_id"],
						task.result["round"],
						task.result["passed"],
						"\n".join(task.result["output"]))
				session.add(chk)

				# Add the round, if it's the last one
				round = task.result["round"]
				self.round_tasks[round].remove(t)
				if len(self.round_tasks[round]) == 0:
					# Update the round
					roundObj = session.query(models.Round).filter(models.Round.number == round).first()
					roundObj.completed = True
					roundObj.finish = datetime.utcnow()

					# Delete from our tracking array
					del self.round_tasks[round]

				# Close and commit
				session.commit()
				session.close()

				task.forget()
				self.tasks.remove(t)

			time.sleep(10)

	def start_round(self, round):
		# Grab all the Team Services that are (currently) enabled
		session = scoring.Session()
		teams = [t.id for t in session.query(models.Team).filter(models.Team.enabled == True).all()]
		services = session.query(models.Service).filter(models.Service.enabled == True).all()
		teamservices = []

		for team in teams:
			for service in services:
				check = {
					"name": service.name,
					"group": service.group,
					"func": service.check,
				}
				teamservices.append(self.buildServiceCheck(session, round, team, service.id, check))

		# Start the round
		session.add(models.Round(round))
		self.round_tasks[round] = []

		# Close our DB session
		session.commit()
		session.close()

		# Shuffle it up
		random.shuffle(teamservices)

		# Create the tasks
		for sc in teamservices:
			task = scoring.worker.check_task.delay(sc)
			self.tasks.append(task.id)
			self.round_tasks[round].append(task.id)

			print("[MASTER] Created Task #{}".format(task.id))

	def buildServiceCheck(self, session, round, team, service, check):
		data = session.query(models.TeamService) \
			.filter(models.TeamService.team_id == team, models.TeamService.service_id == service) \
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

