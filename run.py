import os
import sys

# Ensure the root directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.main import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, port=port)
