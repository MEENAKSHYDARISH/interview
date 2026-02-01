# AI Interviewer

An AI-powered interview platform built with Flask.

## Features
- AI Interviewer Bot (Mock)
- Student Role Selection
- Live Video Interface (WebRTC)
- Student Registration & Login

## Setup

1.  Create a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Run the application:
    ```bash
    python run.py
    ```

4.  Open [http://localhost:5000](http://localhost:5000).

## Configuration
- `database.json`: Stores user and role data locally.
- `OPENAI_API_KEY`: Set this environment variable for real AI responses.
