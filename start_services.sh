#!/bin/bash
cd /root/project/ARX-v2.0
nohup python3 -u auto_monitor_v7.py > auto_monitor_v7.log 2>&1 &
cd backend
nohup ./venv/bin/python3 run_priority_crawl.py > crawl_priority.log 2>&1 &
