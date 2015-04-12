import thread
import time
import sys
from team import Team
from check import Check

"""
Master Thread Object

    - responsible for managing each "teams" thread
    - prints to system out
"""
class Master(object):    
    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.checksPaused = False
    
    def addScore(self, team, service, status, output):
        self.db.addScore(team, service, status, output)
    
    def createTeamThreads(self):
        teams = self.db.getTeams()
        
        for team in teams:
            self.createTeamThread(team['id'], team['name'])
    
    def createTeamThread(self, id, name):
        team = Team(self, id, name)
        
        thread.start_new_thread(team.main, ())
    
    def createTeamChecks(self, team_id):
        checks = self.db.getTeamServices(team_id)
        
        for check in checks:
            self.log("Master", "Creating check thread for Team ID %s" % (team_id))
            self.createCheckThread(team_id, check['id'], check['name'], check['module'], check['args'])
    
    def createCheckThread(self, teamid, serviceid, name, module_name, args):
        module = self.config['scripts'] % (module_name)
        check = Check(self, teamid, serviceid, name, module, args)
        
        thread.start_new_thread(check.main, ())
    
    def log(self, who, text):
        str = "[%s] %s: %s\n" % (time.strftime("%I:%M:%S"), who.upper(), text)
        sys.stdout.write(str)
        sys.stdout.flush()
