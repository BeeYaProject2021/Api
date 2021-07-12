from __future__ import absolute_import, unicode_literals

import os
from celery import shared_task

@shared_task
def RunUserData(path):
    # with open(path + "/combine.py", "r") as r:
    #     exec(r.read())
    os.system(f"python3 {path}/combine.py")

@shared_task
def add(x, y):
    print(x + y) 