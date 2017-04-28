from billiard.exceptions import SoftTimeLimitExceeded
from scoring import celery_app
from scoring.logger import logger
import importlib


@celery_app.task(soft_time_limit=30)
def check_task(sc):
	return check(sc).export()


def check(sc):
	service = ServiceConfig(sc)

	try:
		logger.debug("Using module '{}'".format(service.module_name))
		service.check()
	except:
		service.setPassed(False)

	return service


class ServiceConfig(object):
	def __init__(self, sc):
		self.service = sc
		group = sc["check"]["group"]
		self.module_name = "scoring.checks.{}".format(group)
		self.function_name = sc["check"]["func"]

	def getConfig(self):
		return self.service["config"]

	def getServiceName(self):
		return self.service["check"]["name"]

	def setPassed(self, res=True):
		self.service["passed"] = res

	def getPassed(self):
		return self.service["passed"]

	def addOutput(self, message):
		self.service["output"].append(message)

	def getOutput(self):
		return "\n".join(self.service["output"])

	def export(self):
		return self.service

	def check(self):
		module = importlib.import_module(self.module_name)
		function = getattr(module, self.function_name)
		function(self, self.getConfig())
