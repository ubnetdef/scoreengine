from billiard.exceptions import SoftTimeLimitExceeded
from scoring import celery_app
import importlib

@celery_app.task(soft_time_limit=30)
def check_task(sc):
	try:
		# Load the check class
		group = importlib.import_module('scoring.checks.{}'.format(sc["check"]["group"]))
		check = getattr(group, sc["check"]["func"])

		service = ServiceConfig(sc)
		check(service, service.getConfig())
	except:
		service.setPassed(False)

	return service.export()

class ServiceConfig(object):
	def __init__(self, sc):
		self.service = sc

	def getConfig(self):
		return self.service["config"]

	def getServiceName(self):
		return self.service["check"]["name"]

	def setPassed(self, res=True):
		self.service["passed"] = res

	def addOutput(self, message):
		self.service["output"].append(message)

	def export(self):
		return self.service