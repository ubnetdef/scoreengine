from datetime import datetime
import importlib
import random
import requests
import signal
import threading
import time

import config
import scoring
import scoring.models as models
import scoring.logger as logger
import scoring.worker

class BaseMaster(object):

	def __init__(self, round):
		logger.main.info("Starting ScoreEngine...")

		self.round = round
		self.round_tasks = {}
		self.sleep_startrange = config.ROUND["time"] - config.ROUND["jitter"]
		self.sleep_endrange = config.ROUND["time"] + config.ROUND["jitter"] + 1
		self.no_more_rounds = False

		# Catch CTRL+C signal
		signal.signal(signal.SIGINT, self.shutdown)

	def shutdown(self, signal_, frame):
		logger.main.warn("Caught CTRL+C. Turning off spawning of additional rounds.")

		self.no_more_rounds = True
		remaining = sum(len(r) for r in self.round_tasks.itervalues())
		logger.main.warn("{} tasks remaining. Waiting for them to finish before shutting down.".format(remaining))

	def build_service_check(self, session, round, team, service, check, official=False):
		data = session.query(models.TeamService) \
			.filter(models.TeamService.team_id == team.id, models.TeamService.service_id == service.id) \
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
			"team_id": team.id,
			"team_name": team.name,
			"service_id": service.id,
			"service_name": service.name,
			"round": round,
			"config": checkData,
			"check": check,
			"passed": False,
			"output": [],
			"official": official,
		}

	def get_team_services(self, session, round, official=False):
		"""Grab all the Team Services that are (currently) enabled"""

		session = scoring.Session()
		teams = session.query(models.Team).filter(models.Team.enabled == True).all()
		services = session.query(models.Service).filter(models.Service.enabled == True).all()
		teamservices = []

		for team in teams:
			for service in services:
				check = {
					"name": service.name,
					"group": service.group,
					"func": service.check,
				}
				teamservices.append(self.build_service_check(session, round, team, service, check, official))

		# Shuffle it up
		random.shuffle(teamservices)

		return teamservices

	def check_passed_hook(self, check):
		if not config.BANK["ENABLED"]:
			return

		r = requests.post("http://{}/internalGiveMoney".format(config.BANK["SERVER"]), data={
			'username': config.BANK["USER"],
			'password': config.BANK["PASS"],
			'team': check["team_id"]
		})
		logger.round.debug("Transferring money to {} for service {} being up".format(
			check["team_name"], check["service_name"]))


class ThreadMaster(BaseMaster):

	def __init__(self, round=0):
		super(ThreadMaster, self).__init__(round)

	def run(self):
		if self.round > 0:
			logger.main.debug("ScoreEngine starting from round #{}".format(self.round + 1))

		while not self.no_more_rounds:
			self.round += 1

			# Let's log
			logger.main.info("Starting round #{}".format(self.round))

			# Start our round thread
			round_thread = threading.Thread(target=self.start_round, args=(self.round,))
			round_thread.start()

			# Go to sleep
			nsecs = random.randrange(self.sleep_startrange, self.sleep_endrange)
			logger.round.debug("Round fired off. Sleeping for {} seconds".format(nsecs))
			time.sleep(nsecs)

	def start_round(self, round):
		# Log it
		logger.round.info("Round thread #{} starting".format(round))

		# Make a new session for this thread
		session = scoring.Session()

		# Get the active services from all active teams
		teamservices = self.get_team_services(session, round, official=True)

		# Create a new round
		self.round_tasks[round] = []
		session.add(models.Round(round))

		# Commit and close the session
		session.commit()
		session.close()

		# Start the checks!
		for ts in teamservices:
			self.round_tasks[round].append(ts)

			check_thread = threading.Thread(target=self.new_check, args=(round, ts))
			check_thread.start()

		logger.round.debug("Round thread #{} completed".format(round))

	def new_check(self, round, ts):
		check = scoring.worker.check(ts)

		session = scoring.Session()

		# Add the check
		session.add(
			models.Check(ts["team_id"], ts["service_id"], round, check.getPassed(), check.getOutput()))

		# Finish the round if it's done
		self.round_tasks[round].remove(ts)
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
		logger.round.info("Round: {} | {} | Service: {} | Passed: {}".format(
			round, ts["team_name"], ts["service_name"], check.getPassed()))

		if finishedRound:
			logger.main.info("Round #{} finished".format(round))

		# Check Passed Hook
		if check.getPassed():
			self.check_passed_hook(check)


class QueueMaster(BaseMaster):

	def __init__(self, round=0):
		super(QueueMaster, self).__init__(round)
		self.tasks = []
		self.reaper = None
		self.trafficgen = None

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
			logger.main.info("Starting round #{}".format(self.round))

			# Start our round thread
			round_thread = threading.Thread(target=self.start_round, args=(self.round,))
			round_thread.start()

			# Go to sleep
			nsecs = random.randrange(self.sleep_startrange, self.sleep_endrange)
			logger.round.debug("Round fired off. Sleeping for {} seconds".format(nsecs))
			time.sleep(nsecs)

		logger.round.debug("Exited main event loop")

	def start_reaper(self):
		while not self.no_more_rounds or len(self.tasks) > 0:
			# Logger
			logger.reaper.debug("Starting new reaping cycle")

			# Iterate over the tasks, check for any that are completed
			for t in self.tasks:
				task = scoring.worker.check_task.AsyncResult(t)

				if task.state == "PENDING":
					continue

				# Log that we're reaping it
				logger.reaper.info("Reaping #{}".format(t))

				# Don't handle logging it
				if not task.result["official"]:
					# Log
					logger.reaper.debug("Task #{} is not an scored task".format(t))

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
					logger.main.info("Round #{} finished".format(round))

					# Delete from our tracking array
					del self.round_tasks[round]

				# Close and commit
				session.commit()
				session.close()

				# Check Passed Hook
				if task.result["passed"]:
					self.check_passed_hook(task.result)

				# Remove from the tasks
				task.forget()
				self.tasks.remove(t)

			logger.reaper.debug("Finished reaping cycle")
			time.sleep(config.ROUND["reaper"])

		logger.reaper.debug("Exited main event loop")

	def start_trafficgen(self):
		while not self.no_more_rounds:
			logger.traffic.debug("Starting a new cycle for traffic generation")

			# This is pretty much a lightweight round
			# Grab all the Team Services that are (currently) enabled
			session = scoring.Session()
			teamservices = self.get_team_services(session, -1)
			session.close()

			# Slice
			gen_amount = config.TRAFFICGEN["amount"]
			teamservices = teamservices[:gen_amount]

			# Create the tasks
			for ts in teamservices:
				task = scoring.worker.check_task.delay(ts)
				self.tasks.append(task.id)
				logger.traffic.info("Created Task #{}".format(task.id))

			logger.traffic.debug("Cycle for traffic generation finished")
			time.sleep(config.TRAFFICGEN["sleep"])

		logger.traffic.debug("Exited main event loop")

	def start_round(self, round):
		# Log it
		logger.round.info("Round thread #{} starting".format(round))

		# Grab all the Team Services that are (currently) enabled
		session = scoring.Session()
		teamservices = self.get_team_services(session, round, official=True)

		# Start the round
		session.add(models.Round(round))
		self.round_tasks[round] = []

		# Commit + close our DB session
		session.commit()
		session.close()

		# Create the tasks
		for ts in teamservices:
			task = scoring.worker.check_task.delay(ts)
			self.tasks.append(task.id)
			self.round_tasks[round].append(task.id)

			logger.round.info("Created Task #{}".format(task.id))

		logger.round.debug("Round thread #{} completed".format(round))
