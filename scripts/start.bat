@echo off
cd /d "%~dp0.."
docker compose up --build -d
echo Kanban Studio is running at http://localhost:8000
