#!/usr/bin/env python

from scoring.database import Database
from scoring.master import Master

db = Database({
    'user': 'score_engine',
    'password': 'scoreengine',
    'host': '192.168.1.110',
    'database': 'scoring',
    'raise_on_warnings': True,
    'buffered': True,
})
master = Master(db, {
    'scripts': '/Users/james/Scripts/ScoreEngine/scripts/%s',
    'interval': 60,
    'ip_changing': False,
    'ip_allocated': [
        '192.168.1.101',
        '192.168.1.67',
        '192.168.1.123',
        '192.168.1.228'
    ],
})

master.createTeamThreads()

while 1:
    pass