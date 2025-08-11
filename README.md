# CRM Application with Celery Setup

This guide provides step-by-step instructions for setting up the CRM application with Celery for asynchronous task processing and Celery Beat for periodic task scheduling.

## Prerequisites

- Python 3.8+
- Django 4.2+
- Redis server
- Git

## Installation and Setup

### 1. Install Redis

#### On Ubuntu/Debian:
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### On macOS (using Homebrew):
```bash
brew install redis
brew services start redis
```

#### On Windows:
Download and install Redis from: https://redis.io/download

#### Verify Redis Installation:
```bash
redis-cli ping
# Should return: PONG
```

### 2. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Django Setup

```bash
# Run database migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Collect static files (if needed)
python manage.py collectstatic --noinput
```

### 4. Celery Beat Database Setup

```bash
# Migrate Celery Beat tables
python manage.py migrate django_celery_beat
```

### 5. Running the Application

#### Terminal 1 - Django Development Server:
```bash
python manage.py runserver
```

#### Terminal 2 - Celery Worker:
```bash
celery -A crm worker -l info
```

#### Terminal 3 - Celery Beat Scheduler:
```bash
celery -A crm beat -l info
```

Alternatively, you can run Celery Beat with the worker in one process:
```bash
celery -A crm worker -B -l info
```

## Verification

### 1. Check Redis Connection:
```bash
redis-cli ping
```

### 2. Test Celery Tasks:

#### From Django Shell:
```bash
python manage.py shell
```

```python
# Test basic Celery functionality
from crm.tasks import test_celery_task
result = test_celery_task.delay()
print(result.get())

# Test report generation manually
from crm.tasks import generate_crm_report
result = generate_crm_report.delay()
print(result.get())
```

### 3. Check Log Files:

#### CRM Report Logs:
```bash
tail -f /tmp/crm_report_log.txt
```

#### Celery Test Logs:
```bash
tail -f /tmp/celery_test_log.txt
```

#### Heartbeat Logs (from cron tasks):
```bash
tail -f /tmp/crm_heartbeat_log.txt
```

#### Low Stock Update Logs:
```bash
tail -f /tmp/low_stock_updates_log.txt
```

### 4. GraphQL Endpoint:
Visit: http://localhost:8000/graphql

Test query:
```graphql
query {
  customers {
    id
    name
    email
  }
  orders {
    id
    totalAmount
    orderDate
  }
}
```

## Scheduled Tasks

### Cron Jobs (django-crontab):
- **Heartbeat Logger**: Every 5 minutes (`*/5 * * * *`)
- **Low Stock Update**: Every 12 hours (`0 */12 * * *`)

### Celery Beat Tasks:
- **CRM Report Generation**: Every Monday at 6:00 AM

## Managing Cron Jobs

### Add cron jobs:
```bash
python manage.py crontab add
```

### List active cron jobs:
```bash
python manage.py crontab show
```

### Remove cron jobs:
```bash
python manage.py crontab remove
```

## Managing Celery Beat Tasks

### Using Django Admin:
1. Go to http://localhost:8000/admin/
2. Navigate to "Django Celery Beat" section
3. Manage "Periodic tasks" and "Crontab schedules"

### Using Django Shell:
```python
from django_celery_beat.models import PeriodicTask, CrontabSchedule

# List all periodic tasks
tasks = PeriodicTask.objects.all()
for task in tasks:
    print(f"{task.name}: {task.enabled}")

# Disable a task
task = PeriodicTask.objects.get(name='generate-crm-report')
task.enabled = False
task.save()
```

## Troubleshooting

### Common Issues:

#### 1. Redis Connection Error:
```bash
# Check if Redis is running
sudo systemctl status redis-server

# Start Redis if not running
sudo systemctl start redis-server
```

#### 2. Celery Worker Not Starting:
```bash
# Check for Python path issues
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run with more verbose output
celery -A crm worker -l debug
```

#### 3. Tasks Not Executing:
```bash
# Check Celery Beat is running
celery -A crm beat -l debug

# Verify task registration
celery -A crm inspect registered
```

#### 4. Permission Issues with Log Files:
```bash
# Ensure /tmp directory is writable
sudo chmod 777 /tmp

# Or create dedicated log directory
mkdir -p logs
chmod 755 logs
```

### Logs and Monitoring:

#### Celery Worker Logs:
Check the terminal where the worker is running for real-time logs.

#### Celery Beat Logs:
Check the terminal where beat is running for scheduling logs.

#### Task Results:
```python
# In Django shell
from celery.result import AsyncResult

# Check task result by ID
result = AsyncResult('task-id-here')
print(result.status)
print(result.result)
```

## Production Deployment

### Using Supervisor (Recommended):

#### Install Supervisor:
```bash
sudo apt install supervisor
```

#### Create Celery Worker Configuration:
```bash
sudo nano /etc/supervisor/conf.d/celery_worker.conf
```

```ini
[program:celery_worker]
command=/path/to/venv/bin/celery -A crm worker -l info
directory=/path/to/project
user=www-data
numprocs=1
stdout_logfile=/var/log/celery/worker.log
stderr_logfile=/var/log/celery/worker.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
killasgroup=true
priority=998
```

#### Create Celery Beat Configuration:
```bash
sudo nano /etc/supervisor/conf.d/celery_beat.conf
```

```ini
[program:celery_beat]
command=/path/to/venv/bin/celery -A crm beat -l info
directory=/path/to/project
user=www-data
numprocs=1
stdout_logfile=/var/log/celery/beat.log
stderr_logfile=/var/log/celery/beat.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
killasgroup=true
priority=999
```

#### Start Services:
```bash
sudo mkdir -p /var/log/celery
sudo chown www-data:www-data /var/log/celery
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start celery_worker
sudo supervisorctl start celery_beat
```

## File Structure

```
crm/
├── __init__.py          # Loads Celery app
├── celery.py           # Celery configuration
├── tasks.py            # Celery tasks
├── settings.py         # Django settings with Celery config
├── models.py           # CRM models
├── schema.py           # GraphQL schema
├── cron.py             # Cron job functions
└── README.md           # This file

requirements.txt        # Python dependencies
```

## Support

For issues or questions:
1. Check the logs first
2. Verify all services are running
3. Test individual components
4. Refer to Django and Celery documentation