# EchoTrap

See [README.md](README.md) for the current integrated frontend, tRPC backend,
Python ML service, local setup, verification commands, and security policy.
python -m uvicorn app.main:app --reload --port 8000
```

### Terminal 2: primary application

```powershell
cd "C:\path\to\ABHIMANYU-CHAKRAVYUHA\Echotrap\app"
npm install --legacy-peer-deps
npm run dev
```

Open the URL printed by Vite, normally `http://localhost:3000`.

For local development without MySQL, no application `.env` file is required;
the app stores runs in memory. For persistent storage, create an untracked
`Echotrap/app/.env` file containing:

```env
APP_ID=echotrap
APP_SECRET=local-development-secret
DATABASE_URL=mysql://user:password@host:3306/database
ML_SERVICE_URL=http://127.0.0.1:8000
```

Never commit `.env` files, API keys, database credentials, or other secrets.

## Verification

```powershell
# Primary app
cd Echotrap/app
npm run check
npm run build

# Python service
cd ../../ml-service
python -m pytest tests/test_api.py -q
```

Useful live checks:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://localhost:3000/api/trpc/ping
```

After submitting an analysis, the result diagnostics should identify the
engine as `python-ml-service` when the ML service handled the request.

## Safety boundary

EchoTrap identifies changes in supplied language. It does not:

- prove that a message is fraudulent,
- prove that one message was forwarded from another,
- verify stock-price outcomes,
- create authoritative evidence from an LLM,
- provide buy, sell, or hold recommendations.

Groq, when enabled, is advisory only. The local pipeline and evidence
limitations remain authoritative.
