# Public demo deployment

- `/` public, browser-only fictional priority queue demo; no backend API calls.
- `/staff` existing staff login and protected dashboard.
- Render build: `pip install -r requirements.txt`
- Render start: `gunicorn run:app`
- Do not publish real patient data, local SQLite databases, credentials or virtual environments.
- For production persistence, configure a hosted database. Render ephemeral disks do not preserve SQLite data across redeploys.
- This demo is educational and not a clinical triage tool.
