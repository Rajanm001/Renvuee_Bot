#!/bin/bash

# Startup script for Render deployment
set -e

echo "Starting Telegram Revenue Copilot services..."

# Set environment variables
export N8N_USER_FOLDER=/app/.n8n
export N8N_LOG_LEVEL=${LOG_LEVEL:-info}
export WEBHOOK_URL=${WEBHOOK_URL:-http://localhost:10000}

# Create n8n config directory
mkdir -p $N8N_USER_FOLDER

# Start Agent A in background
echo "Starting Agent A (Knowledge)..."
cd /app/agents/agentA_knowledge
python -m uvicorn app:app --host 0.0.0.0 --port 8001 &
AGENT_A_PID=$!

# Start Agent B in background  
echo "Starting Agent B (Dealflow)..."
cd /app/agents/agentB_dealflow
python -m uvicorn app:app --host 0.0.0.0 --port 8002 &
AGENT_B_PID=$!

# Start Intent Classifier in background
echo "Starting Intent Classifier..."
cd /app/agents/intent_classifier
python -m uvicorn app:app --host 0.0.0.0 --port 8003 &
INTENT_PID=$!

# Wait for agents to start
echo "Waiting for agents to start..."
sleep 10

# Check if agents are healthy
curl -f http://localhost:8001/health || exit 1
curl -f http://localhost:8002/health || exit 1  
curl -f http://localhost:8003/health || exit 1

# Start n8n
echo "Starting n8n orchestrator..."
cd /app
n8n start --tunnel &
N8N_PID=$!

# Wait for n8n to start
sleep 15

# Import workflows if they exist
if [ -d "/app/n8n/workflows" ]; then
    echo "Importing n8n workflows..."
    for workflow in /app/n8n/workflows/*.json; do
        if [ -f "$workflow" ]; then
            echo "Importing $workflow..."
            # n8n import:workflow --input="$workflow" || echo "Failed to import $workflow"
        fi
    done
fi

# Function to cleanup on exit
cleanup() {
    echo "Shutting down services..."
    kill $AGENT_A_PID $AGENT_B_PID $INTENT_PID $N8N_PID 2>/dev/null || true
    wait
}

# Trap signals for cleanup
trap cleanup SIGTERM SIGINT

# Keep the script running and monitor processes
while true; do
    # Check if any process died
    if ! kill -0 $AGENT_A_PID 2>/dev/null; then
        echo "Agent A died, restarting..."
        cd /app/agents/agentA_knowledge
        python -m uvicorn app:app --host 0.0.0.0 --port 8001 &
        AGENT_A_PID=$!
    fi
    
    if ! kill -0 $AGENT_B_PID 2>/dev/null; then
        echo "Agent B died, restarting..."
        cd /app/agents/agentB_dealflow
        python -m uvicorn app:app --host 0.0.0.0 --port 8002 &
        AGENT_B_PID=$!
    fi
    
    if ! kill -0 $INTENT_PID 2>/dev/null; then
        echo "Intent Classifier died, restarting..."
        cd /app/agents/intent_classifier
        python -m uvicorn app:app --host 0.0.0.0 --port 8003 &
        INTENT_PID=$!
    fi
    
    if ! kill -0 $N8N_PID 2>/dev/null; then
        echo "n8n died, restarting..."
        cd /app
        n8n start --tunnel &
        N8N_PID=$!
    fi
    
    sleep 30
done