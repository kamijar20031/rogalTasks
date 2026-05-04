#!/bin/bash

cd ~/projekty/rogalTasks
source backend/venv/bin/activate
cd frontend
touch output.log
serve -s dist -l 3000 > output.log 2>&1 &
cd ../backend
touch output.log
gunicorn --bind 192.168.1.101:5000 wsgi:app > ~/projekty/rogalTasks/backend/output.log 2>&1 &
