#!/usr/bin/env python

from scoring.database import Database
from scoring.master import Master

from scoring.check import Check

db = Database({
    'user': 'score_engine',
    'password': 'scoreengine',
    'host': '192.168.1.110',
    'database': 'scoring',
    'raise_on_warnings': True,
})
master = Master(db, {
    'scripts': '/Users/james/Scripts/ScoreEngine/scripts/%s',
})

master.createTeamThreads()

while 1:
    pass