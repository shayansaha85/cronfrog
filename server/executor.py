import asyncio
import os
import json
from datetime import datetime
from .database import create_job_run, update_job_run, update_job_status, get_job

active_processes = {}
active_logs = {}
run_websockets = {}

async def broadcast_log(run_id, log_type, data):
    if run_id in active_logs:
        active_logs[run_id].append({"type": log_type, "data": data})
    if run_id in run_websockets:
        message = json.dumps({"type": log_type, "data": data})
        for ws in run_websockets[run_id]:
            try:
                await ws.send_text(message)
            except:
                pass

async def read_stream(stream, run_id, log_type):
    while True:
        try:
            line = await stream.readline()
        except ValueError:
            # line too long
            line = await stream.read(1024)
        if not line:
            break
        text = line.decode('utf-8', errors='replace')
        await broadcast_log(run_id, log_type, text)

async def execute_job(job_id):
    job = get_job(job_id)
    if not job:
        return
    
    run_id = create_job_run(job_id, status='running')
    active_logs[run_id] = []
    
    start_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    update_job_status(job_id, start_time, 'running')
    
    env = os.environ.copy()
    if job.get('env_vars'):
        try:
            env_vars = json.loads(job['env_vars'])
            env.update(env_vars)
        except Exception:
            pass
            
    cwd = job.get('working_directory')
    if cwd:
        cwd = cwd.strip()
    if not cwd:
        cwd = None

    command = job['command']
    shell_param = job.get('shell')
    if not shell_param:
        shell_param = 'cmd.exe' if os.name == 'nt' else '/bin/sh'

    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
            executable=shell_param if (os.name != 'nt' or shell_param != 'cmd.exe') else None
        )
            
        active_processes[run_id] = process
        
        await asyncio.gather(
            read_stream(process.stdout, run_id, 'stdout'),
            read_stream(process.stderr, run_id, 'stderr')
        )
        
        await process.wait()
        exit_code = process.returncode
        status = 'success' if exit_code == 0 else 'failed'
        
    except Exception as e:
        error_msg = str(e)
        if isinstance(e, FileNotFoundError):
            if cwd and not os.path.exists(cwd):
                error_msg = f"[Errno 2] No such file or directory: Working directory does not exist: '{cwd}'"
            else:
                error_msg = f"[Errno 2] No such file or directory: Shell executable not found: '{shell_param}'"
        
        await broadcast_log(run_id, 'stderr', f'Error starting process: {error_msg}\n')
        exit_code = -1
        status = 'failed'
        
    finally:
        full_stdout = "".join([l['data'] for l in active_logs.get(run_id, []) if l['type'] == 'stdout'])
        full_stderr = "".join([l['data'] for l in active_logs.get(run_id, []) if l['type'] == 'stderr'])
        
        finished_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        update_job_run(run_id, status, exit_code, full_stdout, full_stderr, finished_at)
        update_job_status(job_id, start_time, status)
        
        if run_id in active_processes:
            del active_processes[run_id]
        if run_id in active_logs:
            del active_logs[run_id]
            
        if run_id in run_websockets:
            close_msg = json.dumps({"type": "close"})
            for ws in run_websockets[run_id]:
                try:
                    await ws.send_text(close_msg)
                    await ws.close()
                except:
                    pass
            del run_websockets[run_id]

async def kill_job_run(run_id):
    if run_id in active_processes:
        process = active_processes[run_id]
        try:
            process.terminate()
            await broadcast_log(run_id, 'stderr', '\n[Process Terminated by User]\n')
        except:
            pass
        return True
    return False

def get_active_log_buffer(run_id):
    if run_id in active_logs:
        return active_logs[run_id]
    return None
