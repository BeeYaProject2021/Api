from __future__ import absolute_import, unicode_literals

import os, threading, time
from celery import shared_task
from subprocess import Popen

# ⚠ DANGER ⚠
# Call run file to train, here are two ways, choose one to run
# with open(path + "/combine.py", "r") as r:
#     exec(r.read())
# os.system(f"python3 {path}/combine.py")

@shared_task
def RunUserData(path, id):
    with open(path + "/combine.py", "r") as r:
        exec(r.read())

    # os.system(f"python3 {path}/combine.py")
    # Popen(path+'/combine.py')

@shared_task
def add(x, y):
    time.sleep(5)
    return x + y