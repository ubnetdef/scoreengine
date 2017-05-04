import random
import requests
import signal

import config
import scoring
import scoring.models as models
import scoring.logger as logger

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
