"""Script pour la Scheduled Task PythonAnywhere :
   python3 /home/riider221/mysite/scheduled_run.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import storage
from tester.runner import run_all

if __name__ == "__main__":
    run = run_all()
    storage.save_run(run)
    print(run["timestamp"], run["summary"])
