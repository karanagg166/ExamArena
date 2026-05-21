import os
import sys

# Add backend directory to Python sys.path so app imports work perfectly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Expose the FastAPI app under the name Vercel expects
from app.main import app
