import os
import sys
import subprocess
import time

# Add the 'backend' directory to the Python path so imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, "backend")
sys.path.insert(0, backend_dir)

print("Starting local Redis server...")
subprocess.run(["redis-server", "--daemonize", "yes"], check=True)
time.sleep(1)

print("Starting Celery worker...")
subprocess.Popen(
    ["celery", "-A", "app.tasks", "worker", "--loglevel=info", "--concurrency=1"],
    cwd=backend_dir
)

print("Starting FastAPI server on port 7860...")
# HuggingFace requires web servers to listen on port 7860
subprocess.run(
    ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"],
    cwd=backend_dir
)
