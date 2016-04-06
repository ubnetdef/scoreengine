from scoring import Session
from scoring.master import Master
from scoring.models import Team, Service
import sys

if len(sys.argv) is not 3:
	sys.exit("Usage: check [team-id] [service-id]")

team_id = int(sys.argv[1])
service_id = int(sys.argv[2])

session = Session()
teamDB = session.query(Team).filter(Team.id == team_id).first()

if not teamDB:
	sys.exit("ERROR: Unknown Team ID")
print "> Team: %s" % (teamDB.name)
team = {
	'id': teamDB.id,
	'name': teamDB.name
}

serviceDB = session.query(Service).filter(Service.id == service_id).first()

if not serviceDB:
	sys.exit("ERROR: Unknown Service ID")
print "> Service: %s" % (serviceDB.name)
service = {
	'id': serviceDB.id,
	'name': serviceDB.name,
	'group': serviceDB.group,
	'check': serviceDB.check
}

master = Master()
master.new_check(team, service)