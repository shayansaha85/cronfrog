import sqlite3
import json
from datetime import datetime
import os
import sys
from pathlib import Path

# Use env var if set, otherwise default to ~/.cronfrog/data/cronfrog.db
# This prevents uvicorn --reload from constantly restarting the server when the db changes.
if os.environ.get('CRONFROG_DB_PATH'):
    DB_PATH = os.environ.get('CRONFROG_DB_PATH')
else:
    home = str(Path.home())
    DB_PATH = os.path.join(home, '.cronfrog', 'data', 'cronfrog.db')

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # Create jobs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            command TEXT NOT NULL,
            cron_expression TEXT,
            timezone TEXT DEFAULT 'UTC',
            enabled BOOLEAN DEFAULT 1,
            working_directory TEXT,
            shell TEXT,
            env_vars TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_run_at TIMESTAMP,
            last_status TEXT
        )
    ''')
    
    # Create job_runs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS job_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            finished_at TIMESTAMP,
            exit_code INTEGER,
            stdout TEXT,
            stderr TEXT,
            status TEXT,
            FOREIGN KEY(job_id) REFERENCES jobs(id)
        )
    ''')
    conn.commit()
    conn.close()

def get_all_jobs():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM jobs ORDER BY id DESC')
    jobs = [dict(row) for row in c.fetchall()]
    for job in jobs:
        job['enabled'] = bool(job['enabled'])
    conn.close()
    return jobs

def get_job(job_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
    row = c.fetchone()
    conn.close()
    if row:
        job = dict(row)
        job['enabled'] = bool(job['enabled'])
        return job
    return None

def create_job(job_data):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO jobs (name, command, cron_expression, timezone, enabled, working_directory, shell, env_vars)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        job_data.get('name'),
        job_data.get('command'),
        job_data.get('cron_expression'),
        job_data.get('timezone', 'UTC'),
        int(job_data.get('enabled', 1)),
        job_data.get('working_directory'),
        job_data.get('shell'),
        job_data.get('env_vars')
    ))
    conn.commit()
    job_id = c.lastrowid
    conn.close()
    return get_job(job_id)

def update_job(job_id, job_data):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        UPDATE jobs 
        SET name = ?, command = ?, cron_expression = ?, timezone = ?, enabled = ?, 
            working_directory = ?, shell = ?, env_vars = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (
        job_data.get('name'),
        job_data.get('command'),
        job_data.get('cron_expression'),
        job_data.get('timezone', 'UTC'),
        int(job_data.get('enabled', 1)),
        job_data.get('working_directory'),
        job_data.get('shell'),
        job_data.get('env_vars'),
        job_id
    ))
    conn.commit()
    conn.close()
    return get_job(job_id)

def delete_job(job_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
    conn.commit()
    conn.close()
    return True

def update_job_status(job_id, last_run_at, last_status):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        UPDATE jobs
        SET last_run_at = ?, last_status = ?
        WHERE id = ?
    ''', (last_run_at, last_status, job_id))
    conn.commit()
    conn.close()

def create_job_run(job_id, status='running'):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO job_runs (job_id, status)
        VALUES (?, ?)
    ''', (job_id, status))
    conn.commit()
    run_id = c.lastrowid
    conn.close()
    return run_id

def update_job_run(run_id, status, exit_code, stdout, stderr, finished_at=None):
    if finished_at is None:
        finished_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        UPDATE job_runs
        SET status = ?, exit_code = ?, stdout = ?, stderr = ?, finished_at = ?
        WHERE id = ?
    ''', (status, exit_code, stdout, stderr, finished_at, run_id))
    conn.commit()
    conn.close()

def get_job_runs(job_id, limit=50):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM job_runs WHERE job_id = ? ORDER BY id DESC LIMIT ?', (job_id, limit))
    runs = [dict(row) for row in c.fetchall()]
    conn.close()
    return runs

def get_job_run(run_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM job_runs WHERE id = ?', (run_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_stats():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) as count FROM jobs')
    total_jobs = c.fetchone()['count']
    c.execute('SELECT COUNT(*) as count FROM jobs WHERE enabled = 1')
    active_jobs = c.fetchone()['count']
    c.execute('SELECT COUNT(*) as count FROM job_runs WHERE status = "failed"')
    failed_runs = c.fetchone()['count']
    conn.close()
    return {
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "failed_runs": failed_runs
    }
