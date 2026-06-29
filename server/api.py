from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import asyncio
from .database import (
    get_all_jobs, get_job, create_job, update_job, delete_job, 
    get_job_runs, get_job_run, get_stats
)
from .scheduler import schedule_job, unschedule_job, get_scheduler_status
from .executor import execute_job, kill_job_run

router = APIRouter(prefix="/api")

@router.get("/jobs")
def api_get_jobs():
    jobs = get_all_jobs()
    sched_status = get_scheduler_status()
    for job in jobs:
        job['next_run_time'] = sched_status.get(job['id'])
    return jobs

@router.post("/jobs")
def api_create_job(job_data: Dict[Any, Any]):
    job = create_job(job_data)
    if job.get('enabled'):
        schedule_job(job)
    return job

@router.get("/jobs/{job_id}")
def api_get_job(job_id: int):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.put("/jobs/{job_id}")
def api_update_job(job_id: int, job_data: Dict[Any, Any]):
    job = update_job(job_id, job_data)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.get('enabled'):
        schedule_job(job)
    else:
        unschedule_job(job_id)
    return job

@router.delete("/jobs/{job_id}")
def api_delete_job(job_id: int):
    unschedule_job(job_id)
    delete_job(job_id)
    return {"status": "success"}

@router.post("/jobs/{job_id}/start")
def api_start_job(job_id: int):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job['enabled'] = True
    job = update_job(job_id, job)
    schedule_job(job)
    return job

@router.post("/jobs/{job_id}/stop")
def api_stop_job(job_id: int):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job['enabled'] = False
    job = update_job(job_id, job)
    unschedule_job(job_id)
    return job

@router.post("/jobs/{job_id}/run")
async def api_run_job(job_id: int):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    asyncio.create_task(execute_job(job_id))
    return {"status": "started"}

@router.post("/jobs/{job_id}/runs/{run_id}/kill")
async def api_kill_job_run(job_id: int, run_id: int):
    success = await kill_job_run(run_id)
    if not success:
        raise HTTPException(status_code=404, detail="Run not found or already finished")
    return {"status": "killed"}

@router.get("/jobs/{job_id}/runs")
def api_get_job_runs(job_id: int):
    return get_job_runs(job_id)

@router.get("/jobs/{job_id}/runs/{run_id}")
def api_get_job_run(job_id: int, run_id: int):
    run = get_job_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@router.get("/stats")
def api_get_stats():
    return get_stats()
