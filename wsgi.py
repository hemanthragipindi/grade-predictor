import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import app as application
app = application

if __name__ == "__main__":
    app.run()
