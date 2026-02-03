import sys
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()


# Add the project root to sys.path so 'app' can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.app import app

if __name__ == '__main__':
    app.run(debug=True, port=5000)
