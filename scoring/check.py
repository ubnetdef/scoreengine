import subprocess

"""
- check thread
    - responsible for calling the bash script, and reporting back to the
team thread
"""
class Check(object):
    
    def __init__(self, master, teamid, serviceid, name, script, args):
        self.master = master
        self.teamid = teamid
        self.serviceid = serviceid
        self.servicename = name
        self.script = script
        self.args = args
    
    def main(self):
        desc_start = "Starting check %s for %d" % (self.servicename, self.teamid)
        desc_end = "Finished check %s for %d" % (self.servicename, self.teamid)
        self.master.log("Check", desc_start)
        
        script = ["/bin/bash", self.script] + self.args
        
        proc = subprocess.Popen(script, executable="/bin/bash", stdout=subprocess.PIPE)
        proc.wait()
        
        output = proc.stdout.read()
        status = proc.returncode
        
        self.master.addScore(self.teamid, self.serviceid, status, output)
        self.master.log("Check", desc_end)