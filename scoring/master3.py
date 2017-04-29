from __future__ import print_function
from datetime import datetime
import importlib
import random
import requests
import signal
import threading
import time

import config
import scoring
from scoring.logger import logger, reaper_logger, round_logger, traffic_logger
import scoring.models as models
import scoring.worker


printLock = threading.Lock()  # Used by OldMaster


class BaseMaster(object):
	def __init__(self, round):
		logger.info("Starting ScoreEngine...")

		self.round = round
		self.round_tasks = {}
		self.sleep_startrange = config.ROUND["time"] - config.ROUND["jitter"]
		self.sleep_endrange = config.ROUND["time"] + config.ROUND["jitter"] + 1

	def buildServiceCheck(self, session, round, team, service, check, official=False):
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
		if "USERPASS" in checkData and "||" in checkData["USERPASS"]:
			checkData["USER"], checkData["PASS"] = checkData["USERPASS"].split("||", 1)

			del checkData["USERPASS"]

		return {
			"team_id": team,
			"service_id": service,
			"round": round,
			"config": checkData,
			"check": check,
			"passed": False,
			"output": [],
			"official": official,
		}

class OldMaster(BaseMaster):

	def __init__(self, round=0):
		super(OldMaster, self).__init__(round)

	def run(self):
		if self.round > 0:
			print("ScoreEngine starting from round #{}".format(self.round + 1))

		while True:
			self.round += 1

			round_thread = threading.Thread(target=self.new_round, args=(self.round,))
			round_thread.start()

			time.sleep(random.randrange(self.sleep_startrange, self.sleep_endrange))

	def new_round(self, round):
		# Make a new session for this thread
		session = scoring.Session()

		# Get all the active teams for this round
		teams = []
		for team in session.query(models.Team).filter(models.Team.enabled == True):
			teams.append({
				'id': team.id,
				'name': team.name
			})

		# Get all active services for this round
		services = []
		for service in session.query(models.Service).filter(models.Service.enabled == True):
			services.append({
				'id': service.id,
				'name': service.name,
				'group': service.group,
				'check': service.check
			})

		# Create a new round
		self.round_tasks[round] = []
		session.add(models.Round(round))

		# Commit and close the session
		session.commit()
		session.close()

		# Start the checks!
		for team in teams:
			for service in services:
				self.round_tasks[round].append((team, service))
				threading.Thread(target=self.new_check, args=(team, service, round)).start()

	def new_check(self, team, service, round, dryRun=False):
		check = {
			"name": service["name"],
			"group": service["group"],
			"func": service["check"]
		}
		session = scoring.Session()
		sc = self.buildServiceCheck(session, round, team["id"], service["id"], check, not dryRun)
		session.close()

		check = scoring.worker.check(sc)

		if dryRun:
			printLock.acquire()
			print("---------[ TEAM: {} | SERVICE: {}".format(team["name"], service["name"]))
			for line in check.getOutput():
				print(line)
			print("---------[ PASSED: {}".format(check.getPassed()))
			printLock.release()
		else:
			session = scoring.Session()

			# Add the check
			session.add(
				models.Check(team["id"], service["id"], round, check.getPassed(), check.getOutput()))

			# Finish the round if it's done
			self.round_tasks[round].remove((team, service))
			finishedRound = False

			if len(self.round_tasks[round]) == 0:
				roundObj = session.query(models.Round).filter(models.Round.number == round).first()
				roundObj.completed = True
				roundObj.finish = datetime.utcnow()

				finishedRound = True

				# Delete from our tracking array
				del self.round_tasks[round]

			# Commit and close
			session.commit()
			session.close()

			# Print out some data
			printLock.acquire()
			print("Round: {:04d} | {} | Service: {} | Passed: {}".format(round, team["name"].ljust(8),
																		 service["name"].ljust(15),
																		 check.getPassed()))

			if finishedRound:
				print("Round: {:04} has been completed!".format(round))
			printLock.release()

			# Tell the Bank API to give some money
			if check.getPassed() and config.BANK["ENABLED"]:
				r = requests.post("http://{}/internalGiveMoney".format(config.BANK["SERVER"]),
								  data={'username': config.BANK["USER"], 'password': config.BANK["PASS"],
										'team': team["id"]})


class NewMaster(BaseMaster):

	def __init__(self, round=0):
		super(NewMaster, self).__init__(round)
		self.tasks = []
		self.reaper = None
		self.trafficgen = None
		self.no_more_rounds = False

		# Catch CTRL+C signal
		signal.signal(signal.SIGINT, self.shutdown)

	def shutdown(self, signal_, frame):
		logger.warn("Caught CTRL+C. Turning off spawning of additional rounds.")

		self.no_more_rounds = True
		logger.warn("{} tasks remaining. Waiting for them to finish before shutting down.".format(len(self.tasks)))

	def run(self):
		# Launch the reaper thread
		self.reaper = threading.Thread(target=self.start_reaper)
		self.reaper.start()

		# Launch the "traffic generator" thread
		self.trafficgen = threading.Thread(target=self.start_trafficgen)
		self.trafficgen.start()

		# Launch the round handler
		self.start_rounds()

	def start_rounds(self):
		while not self.no_more_rounds:
			self.round += 1

			# Let's log
			logger.info("Starting round #{}".format(self.round))

			# Start our round thread
			round_thread = threading.Thread(target=self.start_round, args=(self.round,))
			round_thread.start()

			# Go to sleep
			nsecs = random.randrange(self.sleep_startrange, self.sleep_endrange)
			round_logger.debug("Round fired off. Sleeping for {} seconds".format(nsecs))
			time.sleep(nsecs)

		round_logger.debug("Exited main event loop")

	def start_reaper(self):
		while not self.no_more_rounds or len(self.tasks) > 0:
			# Logger
			reaper_logger.debug("Starting new reaping cycle")

			# Iterate over the tasks, check for any that are completed
			for t in self.tasks:
				task = scoring.worker.check_task.AsyncResult(t)

				if task.state == "PENDING":
					continue

				# Log that we're reaping it
				reaper_logger.info("Reaping #{}".format(t))

				# Don't handle logging it
				if not task.result["official"]:
					# Log
					reaper_logger.debug("Task #{} is not an scored task".format(t))

					# Remove from the tasks
					task.forget()
					self.tasks.remove(t)

					continue

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

					# Log
					logger.info("Round #{} finished".format(round))

					# Delete from our tracking array
					del self.round_tasks[round]

				# Close and commit
				session.commit()
				session.close()

				# Bank Hook
				# Tell the Bank API to give some money
				if task.result["passed"] and config.BANK["ENABLED"]:
					requests.post("http://{}/internalGiveMoney".format(config.BANK["SERVER"]), data={
						'username': config.BANK["USER"],
						'password': config.BANK["PASS"],
						'team': task.result["team_id"]
					})

				# Remove from the tasks
				task.forget()
				self.tasks.remove(t)

			reaper_logger.debug("Finished reaping cycle")
			time.sleep(config.ROUND["reaper"])

		reaper_logger.debug("Exited main event loop")

	def start_trafficgen(self):
		while not self.no_more_rounds:
			traffic_logger.debug("Starting a new cycle for traffic generation")

			# This is pretty much a lightweight round
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
					teamservices.append(self.buildServiceCheck(session, -1, team, service.id, check))

			# Close our DB session
			session.close()

			# Shuffle it up
			random.shuffle(teamservices)

			# Slice
			gen_amount = config.TRAFFICGEN["amount"]
			teamservices = teamservices[:gen_amount]

			# Create the tasks
			for sc in teamservices:
				task = scoring.worker.check_task.delay(sc)
				self.tasks.append(task.id)
				traffic_logger.info("Created Task #{}".format(task.id))

			traffic_logger.debug("Cycle for traffic generation finished")
			time.sleep(config.TRAFFICGEN["sleep"])

		traffic_logger.debug("Exited main event loop")

	def start_round(self, round):
		# Log it
		round_logger.info("Round thread #{} starting".format(round))

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
				teamservices.append(self.buildServiceCheck(session, round, team, service.id, check, official=True))

		# Start the round
		session.add(models.Round(round))
		self.round_tasks[round] = []

		# Commit + close our DB session
		session.commit()
		session.close()

		# Shuffle it up
		random.shuffle(teamservices)

		# Create the tasks
		for sc in teamservices:
			task = scoring.worker.check_task.delay(sc)
			self.tasks.append(task.id)
			self.round_tasks[round].append(task.id)

			round_logger.info("Created Task #{}".format(task.id))

		round_logger.debug("Round thread #{} completed".format(round))
