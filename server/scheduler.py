import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from .database import get_all_jobs
from .executor import execute_job

scheduler = AsyncIOScheduler()

def schedule_job(job):
    if not job.get('enabled') or not job.get('cron_expression'):
        return
        
    job_id = str(job['id'])
    
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        
    try:
        trigger = CronTrigger.from_crontab(job['cron_expression'])
        scheduler.add_job(
            execute_job,
            trigger=trigger,
            args=[job['id']],
            id=job_id,
            name=job['name']
        )
    except Exception as e:
        print(f"Error scheduling job {job['id']}: {e}")

def unschedule_job(job_id):
    job_id_str = str(job_id)
    if scheduler.get_job(job_id_str):
        scheduler.remove_job(job_id_str)

def load_jobs_into_scheduler():
    jobs = get_all_jobs()
    for job in jobs:
        if job.get('enabled'):
            schedule_job(job)

import datetime

def get_scheduler_status():
    jobs_status = {}
    for job in scheduler.get_jobs():
        if job.next_run_time:
            utc_time = job.next_run_time.astimezone(datetime.timezone.utc)
            jobs_status[int(job.id)] = utc_time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            jobs_status[int(job.id)] = None
    return jobs_status
