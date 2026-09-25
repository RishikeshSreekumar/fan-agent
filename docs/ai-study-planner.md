# AI ceiling-fan study planner

Implemented 2026-09-21. Gemini (default) and OpenAI API transports and UI are implemented; live Gemini 2.5 Flash extraction passed the three recorded smoke scenarios after a prompt correction.

## Start locally

Stop the old Fan-Agent server if it occupies port 8765. In PowerShell, from the fan-agent directory:

```powershell
& "D:\AI assisted simulation\Foam-Agent-main\fan-agent\start-ai.ps1" -Model "gemini-2.5-flash"
```

Run the command above, not the contents of the script. It works from any PowerShell folder. The supplied model ID is the user-selected model; live access remains to be verified.

The helper prompts for a hidden Gemini API key and a model ID supporting Gemini structured outputs. It does not save the key to disk; it supplies credentials to the server process and restores previous environment settings on exit. Use an API key with access to the selected model. An alternative is setting GEMINI_API_KEY, FAN_AGENT_AI_PROVIDER=gemini and FAN_AGENT_AI_MODEL in the server environment and using start.ps1. Do not put keys into chat, browser fields or source files.

OpenAI remains optional via `./start-ai.ps1 -Provider openai` with its own key and model. You do not need an OpenAI key for Gemini.

Open http://127.0.0.1:8765 and select **AI study planner**. The existing app needs a restart to load the new backend.

Try:

> Compare a 1200 mm ceiling fan at 250 and 300 RPM in a 4 m by 4 m by 3 m room. Rotor height is 2.5 m above the floor; sampling height is 1.2 m above the floor. Rotation is clockwise viewed from above.

Expected: two parameter proposals, with geometry still needed locally. Review all extracted values, choose a case to copy into the design form, attach/confirm the local geometry, and use the existing save action. No case is saved automatically. Download proposal exports the result as JSON.

A short request such as “Compare this fan at 250 and 300 RPM” should identify missing dimensions and direction. Add those details to the text and submit again. This first version is single-turn; it does not read the current form or previous requests.

## Implemented boundaries

- One API request per submission, 45-second network timeout, 1,800 output-token cap, bounded response size and one concurrent generation per server. No automatic retry.
- Only the typed prompt is sent, with fixed extraction instructions/schema. No CAD files, saved cases, API secrets or solver logs are included in the prompt. The OpenAI adapter sets store=false. Gemini uses its native generateContent endpoint; provider data policies apply.
- Strict structured output plus independent finite-number, shape, range and dimension checks. Complete proposed cases must pass existing validate_case. Limits are sanity bounds, not a qualified design envelope.
- One to four RPM cases for the same ceiling fan and room. Unsupported requests are shown separately; the model is instructed not to invent missing fields. Semantic extraction still requires designer review; schema checks cannot prove the model interpreted language correctly.
- No model-generated commands, solver selection, mesh changes, result predictions or execution tools. Every response has can_run=false and results=null.
- Explicit configuration, refusal, incomplete-output, malformed-output and provider-error states. Provider response bodies and credentials are not exposed in errors.
- Proposals are held in the browser until downloaded or copied to the design form. Saved case behavior remains unchanged.

## Foam-Agent reuse

Inspected upstream src/nodes/planner_node.py and src/utils.py LLMService.invoke. Adapted its separation of system/user input and schema-constrained planning, followed by validation. No upstream runtime is imported and no upstream code was copied. Its planner chooses solvers, retrieves tutorials and creates/cleans case directories; those responsibilities are outside this proposal-only feature. The existing v2412 development runtime remains separate from upstream Foundation 10 assumptions.

Gemini format checked against [Google generateContent documentation](https://ai.google.dev/api/generate-content). Gemini blocked, truncated and malformed responses are rejected; no automatic fallback sends data to another provider.

OpenAI API format checked against [official Structured Outputs documentation](https://developers.openai.com/api/docs/guides/structured-outputs).

## Verification

- 65 Python tests pass, including 14 proposal/transport/HTTP tests.
- JavaScript syntax check passes.
- Headless Edge smoke test passes: configuration gate, mocked proposal render, transfer of the 300 RPM case into the design form, no saved cases and no JavaScript errors.
- API responses were mocked in automated tests. The original automated tests used mocks. Subsequent live verification made six generic model calls across two rounds; no new solver run or engineering validation was performed.

Live smoke verification is complete for the three scenarios recorded below. Broader extraction reliability is not established.

## First live check

Gemini 2.5 Flash responded to three generic prompts. Two passed; the complete comparison was incorrectly classified unsupported. See ai-live-checks/20260921T184435239329Z.json. The extraction prompt now explicitly allows RPM comparisons. Restart the server before rechecking with `python scripts/check-live-ai.py`. This script sends at most three model requests and writes timestamped evidence; it does not load CAD or start simulations. Corrected-prompt live verification is pending.

### Corrected prompt: passed

[Live evidence](ai-live-checks/20260921T184638173355Z.json): complete comparison PASS, missing-input handling PASS, unsupported-work handling PASS. All outputs retained can_run=false and results=null. Initial failure remains archived. Test prompts used generic ceiling-fan dimensions only.
