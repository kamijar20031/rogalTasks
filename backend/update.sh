#!/bin/bash

cd /home/rogal/projekty/rogalTasks/backend
source venv/bin/activate
current_date=$(date +"%Y-%m-%d %H:%M:%S")
echo "Current date: $current_date" >> output.txt
python3 harmo.py >> output.txt 
deactivate
