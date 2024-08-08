#!/bin/sh
echo "Sleep 3 seconds and run alembic on database"
#sleep 3
alembic upgrade head

echo "Running uvicorn on api server"
python3 -m uvicorn api.server:app --port=8000 --host=0.0.0.0
