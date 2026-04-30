# CV Automation Backend

FastAPI backend that wraps the CV automation script as an HTTP API.

## Structure

```
backend/
  main.py                        # FastAPI app and routes
  master_cv.json                 # Your master CV source of truth
  requirements.txt
  services/
    claude_service.py            # Claude API logic
    document_service.py          # Node.js formatter subprocess calls
  formatters/
    format_cv.js                 # Word doc CV formatter
    format_cover_letter.js       # Word doc cover letter formatter
  outputs/                       # Generated zips land here (gitignored)
```

## Setup

1. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Install Node dependencies (docx package):
   ```
   npm install docx
   ```

3. Copy `.env.example` to `.env` and add your Anthropic API key:
   ```
   cp .env.example .env
   ```

4. Set the environment variable before running:
   - Windows (PowerShell): `$env:ANTHROPIC_API_KEY="your_key_here"`
   - Mac/Linux: `export ANTHROPIC_API_KEY="your_key_here"`

## Running locally

```
uvicorn main:app --reload --port 8000
```

## Endpoints

### GET /health
Returns `{"status": "ok"}`. Use this to confirm the server is running.

### POST /generate
Accepts a JSON body and returns a zip file containing the tailored CV and cover letter.

**Request:**
```json
{
  "job_description": "Paste the full job description here"
}
```

**Response:**
A zip file download containing:
- `CV_RoleTitle_Company.docx`
- `CoverLetter_RoleTitle_Company.docx`

**Example with curl:**
```
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"job_description": "We are looking for a backend developer..."}' \
  --output application.zip
```

## Notes

- `outputs/` is where generated files land temporarily. Add it to `.gitignore`.
- The Node.js formatters are called as subprocesses. Node must be installed and `docx` must be available via `npm install docx` in the project root.
- Update `master_cv.json` as your experience grows. The API always reads from it fresh on each request.
