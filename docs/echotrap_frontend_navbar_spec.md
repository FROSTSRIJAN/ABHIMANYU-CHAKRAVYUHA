# EchoTrap Frontend Navbar and Multi-Page Structure

## Product summary
EchoTrap is a claim-mutation intelligence dashboard for analyzing how a financial message changes across a sequence of related communications. The frontend should support investigation, explanation, and safety-first decision support without presenting the output as proof of fraud.

## Navigation model
Use a multi-page navigation system with a persistent top navbar and page-specific sections.

### Navbar items
- Home
- Analyzer
- Results
- Safety Guide
- Model Diagnostics
- Docs / About

### Navbar behavior
- Sticky top bar on all pages
- Brand on left
- Section links on right
- Language toggle in the top-right: EN / हिं
- Mobile menu collapses into a hamburger menu

## Page structure
### 1. Home page
Purpose: explain the product and motivate the user.

Sections:
- Hero banner
- Why EchoTrap
- Example mutation flow
- CTA buttons
- Compliance note

### 2. Analyzer page
Purpose: input the message sequence.

Sections:
- page heading
- message cards (2–5)
- add/remove buttons
- validation summary
- Run Analysis button

### 3. Processing page
Purpose: show active analysis.

Sections:
- animated processing indicator
- step list
- status note

### 4. Results page
Purpose: show the signal report.

Sections:
- summary banner
- claim evolution timeline
- mutation list
- signal cards
- plain-language explanation
- safety next steps

### 5. Safety Guide page
Purpose: explain limitations.

Sections:
- what this tool does and does not do
- due diligence checklist
- verification guidance

### 6. Diagnostics page
Purpose: expose the ML pipeline state.

Sections:
- model status
- semantic similarity scores
- certainty shift summary
- urgency shift summary
- fallback model note

## UX design rules
- Use dark theme with strong contrast
- Use risk colors carefully: neutral, watch, strong
- Keep all claims framed as language risk analysis, not fraud proof
- Show disclaimers prominently
- Prefer clarity over hype

## Proposed route map
- / -> Home
- /analyze -> Analyzer
- /processing -> Processing
- /results -> Results
- /safety -> Safety Guide
- /diagnostics -> Model Diagnostics

## Implementation recommendation
Use React + TypeScript + Vite, with a shared top navbar and route-level layouts. Keep all results in a single normalized contract from the backend.

## Final note
This navigation and page structure should match the actual backend capabilities already present in the project: sequence input, mutation detection, similarity comparison, verification, and explanation output.
