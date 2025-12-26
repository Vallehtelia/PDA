# Orja (terminal-first assistant, English)

Terminal-focused assistant for Raspberry Pi that uses a local llama.cpp model. Wake phrase is `hey slave`. Audio and cloud LLM integrations remain placeholders.

## Quick start (Raspberry Pi 4, Python 3.11+)
1) Install llama.cpp  
```bash
cd /home/ylivoittamaton/PDA
./scripts/install_llama_cpp.sh
```
2) Download a model  
- SmolLM2-360M (~0.27GB, recommended): `./scripts/download_model_smollm2.sh`  
- Qwen2.5-0.5B (~0.3GB): `./scripts/download_model_qwen25.sh`

3) Install Python deps  
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4) Run the assistant  
```bash
python -m orja
```

## Usage
- Start every command with the wake phrase: `hey slave ...`
- Examples:
  - `hey slave time`
  - `hey slave help`
  - `hey slave timer 5 minutes`
  - `hey slave tell me a joke`

## Pipeline overview
Each request flows through:
1) **EvaluatorAgent** – labels difficulty and whether cloud might be needed (JSON).  
2) **RouterAgent** – chooses `skill` vs `chat` and skill arguments (JSON).  
3) **Skill** – runs if selected (time/help/timer placeholder).  
4) **ResponderAgent** – crafts the final English reply, using any skill result.

All steps are logged to `logs/orja.log` and stored in SQLite table `pipeline_events` for traceability.

## Prompts (editable)
Located in `prompts/`:
- `evaluator_system.txt`
- `router_system.txt`
- `responder_system.txt`
- `skill_summaries.txt` (describes available skills and invocation hints)

Hot reload: set `dev.reload_prompts: true` (default) and edits are picked up on the next request.
Add new agent: create a prompt file, add an agent under `orja/agents/`, and wire it into `orja/core/pipeline.py`.

## Skills
- `time`: returns current time in Finland.
- `help`: lists available commands and the wake phrase.
- `timer`: placeholder timer; tries to read minutes if provided.
Anything else falls back to the LLM chat path.

## Configuration (`config/config.yaml`)
- `assistant.wake_phrase`: `hey slave`
- `pipeline.enabled`: toggle multi-step pipeline (default on)
- `pipeline.max_history_messages`: number of past messages passed to agents
- `agents.{evaluator,router,responder}.max_tokens`: per-agent token caps
- `dev.reload_prompts`: hot-reload prompt files (default true)
- `llm.backend`: `llama_cpp_cli` or `placeholder`
- `llm.llama_cpp.*`: paths and parameters for llama-cli/server
- `llm.system_prompt`: base system prompt (agent-specific prompts are in `prompts/`)
- `llm.json_strict`: hint for JSON-style generations
Environment overrides: prefix vars with `ORJA_` (e.g., `ORJA_LLM__BACKEND=placeholder`).

## Data and logs
- SQLite memory + pipeline events: `data/orja.sqlite` (auto-created)
- Logs: `logs/orja.log`
- Models: `models/`
- llama.cpp checkout/build: `vendor/llama.cpp/`

## Validation checklist
- `vendor/llama.cpp/build/bin/llama-cli --help` works
- A GGUF model exists in `models/`
- `python -m orja` starts and prints the wake phrase hint
- `hey slave time` prints the current time
- `hey slave help` lists commands
- `hey slave timer 5 minutes` returns a placeholder timer response
- `data/orja.sqlite` and `logs/orja.log` are created after first run

