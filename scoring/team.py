import time

"""
Master Thread Object

    - responsible for creating new "check" threads
    - reports to master thread a check
"""

class Team(object):
    
    def __init__(self, master, id, name):
        self.master = master
        self.id = id
        self.name = name
    
    def main(self):
        self.master.log("Team", "%s management thread started" % self.name)
        
        while 1:
            self.master.log("Team", "Starting checks for %s" % self.name)
            self.master.createTeamChecks(self.id)
            
            time.sleep(self.master.config['interval'])
