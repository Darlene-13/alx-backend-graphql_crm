"""
Celery configuration for CRM project.

This module sets up the Celery application for handling asynchronous tasks
and periodic task scheduling with Celery Beat.
"""

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')

# Create the Celery application instance
app = Celery('crm')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Optional: Add debugging task for testing
@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    print(f'Request: {self.request!r}')
    return 'Celery is working!'


# Optional: Task routing configuration
app.conf.task_routes = {
    'crm.tasks.generate_crm_report': {'queue': 'reports'},
    'crm.tasks.*': {'queue': 'default'},
}

# Optional: Queue configuration
app.conf.task_default_queue = 'default'
app.conf.task_queues = {
    'default': {
        'exchange': 'default',
        'exchange_type': 'direct',
        'routing_key': 'default',
    },
    'reports': {
        'exchange': 'reports',
        'exchange_type': 'direct',
        'routing_key': 'reports',
    },
}

# Health check configuration
app.conf.worker_send_task_events = True
app.conf.task_send_sent_event = True

# Logging configuration for Celery
app.conf.worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
app.conf.worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

# Error handling
app.conf.task_soft_time_limit = 60
app.conf.task_time_limit = 120
app.conf.task_acks_late = True
app.conf.worker_prefetch_multiplier = 1

if __name__ == '__main__':
    app.start()