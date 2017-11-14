#!/bin/bash

gunicorn --bind 0.0.0.0:8080 --daemon --pid app.pid --workers 1 --error-logfile=error.log server:app
