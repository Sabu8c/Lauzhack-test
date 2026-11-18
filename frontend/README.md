# Frontend

Static web client with zero dependencies and no build step.

## Local Development
Run the local HTTP server from the project root:
```bash
python3 -m http.server 5173 --directory frontend
```
The API target URL is configured via `window.API_BASE` in `config.js`.
