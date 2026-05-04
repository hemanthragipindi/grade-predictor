import os
import sys

# Add backend folder to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
sys.path.insert(0, BACKEND_DIR)

print(f"WSGI DEBUG: Base Dir: {BASE_DIR}")
print(f"WSGI DEBUG: Backend Dir: {BACKEND_DIR}")

try:
    from app import app
    print("WSGI DEBUG: App imported successfully.")
except Exception as e:
    print(f"WSGI DEBUG: IMPORT FAILED! {e}")
    import traceback
    traceback.print_exc()
    raise e

if __name__ == "__main__":
    app.run()
