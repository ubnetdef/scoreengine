import thread
import time
import sys
from team import Team
from check import Check

"""
- master thread
    - responsible for managing each "teams" thread
    - prints to system out
    - handles db connection
"""
class Master(object):    
    def __init__(self, db, config):
        self.db = db
        self.config = config
    
    def addScore(self, team, service, status, output):
        query = "INSERT INTO checks(team_id, service_id, status, output)" \
                "VALUES (%s, %s, %s, %s)"
        args = (team, service, status, output)
                
        conn = self.db.conn
        cursor = conn.cursor()
        cursor.execute(query, args)
        conn.commit()
        
        cursor.close()
    
    def createTeamThreads(self):
        conn = self.db.conn
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM teams")
        
        row = cursor.fetchone()
        
        while row is not None:
            team_id = row[0]
            team_name = row[1]
            
            self.createTeamThread(team_id, team_name)
            
            row = cursor.fetchone()
        
        cursor.close()
    
    def createTeamThread(self, id, name):
        team = Team(self, id, name)
        
        thread.start_new_thread(team.main, ())
    
    def createTeamChecks(self, team_id):
        conn = self.db.conn
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM services")
        
        row = cursor.fetchone()
        
        while row is not None:
            service_id = row[0]
            service_name = row[1]
            module = row[2]
            
            data = conn.cursor()
            data.execute("SELECT `value` FROM services_data WHERE team_id = %s AND service_id = %s ORDER BY `order` ASC", (team_id, service_id))
            
            args = []
            dataRow = data.fetchone()
            
            while dataRow is not None:
                args.append(dataRow[0])
                
                row = data.fetchone()
            
            self.createCheckThread(team_id, service_id, service_name, module, args)
            
            row = cursor.fetchone()
        
        cursor.close()
    
    def createCheckThread(self, teamid, serviceid, name, module_name, args):
        module = self.config['scripts'] % (module_name)
        check = Check(self, teamid, serviceid, name, module, args)
        
        thread.start_new_thread(check.main, ())
    
    def log(self, who, text):
        str = "[%s] %s: %s\n" % (time.strftime("%I:%M:%S"), who, text)
        sys.stdout.write(str)
        sys.stdout.flush()
