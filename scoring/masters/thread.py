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

class ThreadMaster(scoring.master.BaseMaster):

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