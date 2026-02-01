# AI Interviewer POC - Running Instructions

This directory contains a full-stack AI Interviewer application consisting of a React frontend and a FastAPI (Python) backend.

## Prerequisites

- Node.js (v18+)
- Python (v3.11+)
- MongoDB (running locally on default port 27017)

## Setup and Fixes Applied

The following fixes were applied to make the codebase runnable:
1.  **Backend Configuration**: Created `Backend/config.py` with default environment variables.
2.  **Dependencies**: Created `Backend/deps.py` with a mock authentication handler and `Backend/requirements.txt`.
3.  **Router Logic**: Updated `Backend/main.py` to import valid routers (`setup_bot`, `hr_roles`, `student_resume`) and removed the missing `interview` module.
4.  **Dockerfile**: Fixed the `COPY` instruction in `Backend/Dockerfile`.

## Running the Application

### 1. Start MongoDB
Ensure you have a MongoDB instance running.
```bash
# If you have docker
docker run -d -p 27017:27017 mongo
# Or run your local installation
mongod --dbpath /path/to/data
```

### 2. Backend Setup
Navigate to the `ai-interviewer` root directory (parent of Backend):
```bash
cd ai-interviewer
# or just stay in the root if you are already there
```

Create a virtual environment:
```bash
python3 -m venv Backend/venv
source Backend/venv/bin/activate
```

Install dependencies:
```bash
pip install -r Backend/requirements.txt
```

Run the server (as a module check):
```bash
uvicorn Backend.main:app --reload --port 8000
```
**Important**: Do NOT run it from inside the `Backend` folder, run it from the root `ai-interviewer` folder so that imports work correctly.

### 3. Frontend Setup
Open a new terminal and navigate to the `frontend` directory:
```bash
cd frontend
```

Install dependencies:
```bash
npm install
```

Run the development server:
```bash
npm run dev
```
The frontend will likely run at `http://localhost:5173`. Open this URL in your browser to test the application.

## Troubleshooting

- **Authentication**: A mock user (HR role) is automatically injected. To test as a student, you may need to modify `Backend/deps.py` to return `role: "student"`.
- **OpenAI Key**: The app requires an OpenAI API Key for some features. Set `OPENAI_API_KEY` in your environment or update `Backend/config.py`.
