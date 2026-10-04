# EchoTrap Frontend — Mock Prototype

A polished, mock-data-only React frontend for the SANGYAN investor-protection hackathon concept **EchoTrap**.

## What works
- Professional landing page
- 2–5 message analyzer
- Load-demo flow
- Validation + add/remove messages
- Simulated NLP processing screen
- Claim-evolution timeline
- Phrase-level highlights with hover explanations
- Mutation cards and language-signal cards
- English/Hindi explanation toggle
- Investor-safety guidance
- Mobile responsive layout
- No backend, database or ML dependency

## Run locally
```bash
npm install
npm run dev
```

Open the local Vite URL shown in the terminal.

## Demo flow
1. Open landing page
2. Click **Analyze message sequence**
3. Demo sequence is already loaded (or click **Load demo sequence**)
4. Click **Run mutation analysis**
5. Wait for simulated processing
6. Review claim evolution, language shifts and safety guidance
7. Use the EN / हिं toggle in the top-right to switch the explanation language

## Integration later
The mock result lives in `src/mockAnalysis.ts`.
When the backend is ready, replace the local result with the backend response while keeping the same data shape.

## Important positioning
EchoTrap identifies changes in supplied language. It does **not**:
- prove that a message is fraudulent,
- prove that one message was forwarded from another,
- verify stock-price outcomes,
- provide buy/sell/hold recommendations.
