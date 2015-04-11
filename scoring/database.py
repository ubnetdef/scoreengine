"""
- database connection
"""

import mysql.connector

class Database(object):    
    def __init__(self, config):
        self.conn = mysql.connector.connect(**config)