import os
import sys
import traceback

# Get the absolute path of the current directory (root)
root_path = os.path.dirname(os.path.abspath(__file__))
# Add the backend directory to the Python path
backend_path = os.path.join(root_path, 'backend')
sys.path.insert(0, backend_path)

print(f"WSGI: Starting up. Root: {root_path}, Backend: {backend_path}")

try:
    # Now we can import app directly because backend_path is in sys.path
    from app import app
    print("WSGI: Application imported successfully.")
except Exception as e:
    print("WSGI: CRITICAL ERROR during import!")
    traceback.print_exc()
    raise e

if __name__ == "__main__":
    app.run()
