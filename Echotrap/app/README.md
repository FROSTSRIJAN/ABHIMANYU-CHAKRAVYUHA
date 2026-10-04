# EchoTrap primary frontend

This is the primary EchoTrap application. It contains the multi-page React
frontend, the tRPC application backend, and the server-side adapter that calls
the Python FastAPI/ML service.

## Architecture

```text
Browser -> React pages -> tRPC analysis.run -> Python ML service
                          \\-> MySQL analysis_runs
```

The analysis mutation calls `ML_SERVICE_URL` first. If the Python service is
unavailable, it uses the local TypeScript engine as an explicit fallback so the
demo remains usable. Results are normalized into `contracts/analysis.ts`,
which powers the Analyzer, Processing, Results, and Diagnostics pages.

## Run locally

1. Start the Python ML service from the repository `ml-service` directory:

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

2. Create a local, untracked `Echotrap/app/.env` file with `DATABASE_URL` and
  `ML_SERVICE_URL=http://127.0.0.1:8000`. Never commit this file or API keys.

3. Install dependencies and start the primary app:

```powershell
npm install
npm run dev
```

Open the Vite URL, then use **Analyzer**. A successful run is stored in the
configured MySQL database and shown at **Results**. The Python service remains
the source of semantic and mutation signals.

## Verification

```powershell
npm run check
npm run build
```

The Python service can be checked independently with:

```powershell
cd ..\..\ml-service
python -m pytest tests/test_api.py -q
```

## Safety boundary

EchoTrap identifies language changes and verification limitations. It does not
prove fraud, establish the truth of a claim, or provide investment advice.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
