from datetime import datetime
import random
import threading
import time

import config
import scoring
import scoring.master
import scoring.models as models
import scoring.logger as logger
import scoring.worker

class QueueMaster(scoring.master.BaseMaster):

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