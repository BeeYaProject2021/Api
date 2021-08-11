from __future__ import absolute_import, unicode_literals

import os, threading, time
from celery import shared_task

Lock = threading.Lock()

# ⚠ DANGER ⚠
# Call run file to train, here are two ways, choose one to run
# with open(path + "/combine.py", "r") as r:
#     exec(r.read())
# os.system(f"python3 {path}/combine.py")

@shared_task
def RunUserData(path, id):
    flag = 0
    with open(path + "/combine.py", "r") as r:
        exec(r.read())

    # os.system(f"python3 {path}/combine.py")
    return flag

@shared_task
def add(x, y):
    time.sleep(5)
    return x + y