# Kanban Studio

A project management MVP with a Kanban board and AI chat. Sign in, manage cards with drag-and-drop, rename columns, and use natural language to create/edit/move cards via the AI sidebar.

**Stack:** Next.js (static export), Python FastAPI, SQLite, Docker. AI via OpenRouter (`openai/gpt-oss-120b`).

## Run locally

1. Create `.env` in project root with:
   ```
   OPENROUTER_API_KEY=your_key
   ```

2. Start the app:
   - Linux/Mac: `./scripts/start.sh`
   - Windows: `scripts\start.bat`

3. Open http://localhost:8000. Login: `user` / `password`.

4. Stop: `./scripts/stop.sh` or `scripts\stop.bat`

Requires Docker (or Podman; scripts auto-detect).
