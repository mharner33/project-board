# Scripts

Start and stop scripts for running the Docker container locally.

## Files (planned)

- `start.sh` / `stop.sh` -- Linux/Mac (bash)
- `start.bat` / `stop.bat` -- Windows (cmd)

## Behavior

- **start**: Build the Docker image (if needed) and run the container, mapping the appropriate port. Reads `.env` from the project root for `OPENROUTER_API_KEY`.
- **stop**: Stop and remove the running container.