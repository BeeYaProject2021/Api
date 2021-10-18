from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
BROKER_URL = 'pyamqp://B04:BFuV+90434@140.136.151.88:5672/api'
BACKEND = 'redis://localhost/0'
# worker_max_tasks_per_child -> for one task per worker and then he die
app = Celery('api', broker=BROKER_URL, worker_max_tasks_per_child=1)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')
# worker_max_tasks_per_child = 1
# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')