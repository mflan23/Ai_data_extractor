#!/bin/bash

# Start the AI Dataset Builder backend

echo "🚀 Starting AI Dataset Builder Backend..."

# Start the server using uv
echo "📡 Server starting on http://localhost:8000"
echo "📚 API docs available at http://localhost:8000/docs"
uv run uvicorn main:app --host 0.0.0.0 --port 8000
