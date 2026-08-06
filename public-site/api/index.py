import sys
from pathlib import Path

# Add parent directory to path so we can import unified.app
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from unified.app import app

# Vercel expects the app to be exported as 'app'
__all__ = ['app']
