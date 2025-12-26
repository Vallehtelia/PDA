# Orja (terminal-first assistant)

Orja is a small, terminal-first assistant for Raspberry Pi. It listens for the wake phrase `hey slave`, runs a local multi-agent pipeline (Evaluator → Router → Skill → Responder), and executes simple skills (time/help/timer placeholder) using a local llama.cpp model. Audio and cloud LLM hooks are placeholders so you can extend them later.

---
## Highlights
- Wake-phrase UX: `hey slave …`
- Local-first: llama.cpp CLI/server, tiny models (SmolLM2/Qwen).
- Multi-agent pipeline with JSON contracts per step.
- Skills with traceability: events logged to SQLite (`pipeline_events`) and file logs.
- Hot-editable prompts in `prompts/` with optional reload-on-change.

---
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

---
## Usage
- Always start with the wake phrase: `hey slave ...`
- Try:
  - `hey slave time`
  - `hey slave help`
  - `hey slave timer 5 minutes`
  - `hey slave tell me a joke`

---
## Pipeline overview
1) **EvaluatorAgent** – labels difficulty and cloud need (JSON).  
2) **RouterAgent** – picks `skill` vs `chat` + arguments (JSON).  
3) **Skill** – executes if chosen (time/help/timer placeholder).  
4) **ResponderAgent** – crafts the final English reply.

All steps log to `logs/orja.log` and persist to SQLite table `pipeline_events`.

---
## Prompts (editable)
Location: `prompts/`
- `evaluator_system.txt`
- `router_system.txt`
- `responder_system.txt`
- `skill_summaries.txt` (skill descriptions and invocation hints)

Hot reload: set `dev.reload_prompts: true` (default); edits load on next request.  
Adding an agent: create a prompt file, add an agent in `orja/agents/`, wire it in `orja/core/pipeline.py`.

---
## Skills
- `time`: current time in Finland.
- `help`: lists commands and the wake phrase.
- `timer`: placeholder timer; reads minutes if provided.
Fallback: any other request goes to the LLM chat path.

---
## Configuration (`config/config.yaml`)
- `assistant.wake_phrase`: `hey slave`
- `pipeline.enabled`: enable/disable pipeline (default on)
- `pipeline.max_history_messages`: history passed to agents
- `agents.{evaluator,router,responder}.max_tokens`: per-agent caps
- `dev.reload_prompts`: hot-reload prompts (default true)
- `llm.backend`: `llama_cpp_cli` or `placeholder`
- `llm.llama_cpp.*`: llama-cli/server paths and params
- `llm.system_prompt`: base system prompt (agent-specific prompts live in `prompts/`)
- `llm.json_strict`: hint to favor JSON outputs
Env overrides: prefix with `ORJA_` (e.g., `ORJA_LLM__BACKEND=placeholder`).

---
## Data and logs
- SQLite memory + pipeline events: `data/orja.sqlite` (auto-created)
- Logs: `logs/orja.log`
- Models: `models/`
- llama.cpp checkout/build: `vendor/llama.cpp/`

---
## Validation checklist
- `vendor/llama.cpp/build/bin/llama-cli --help` works
- A GGUF model exists in `models/`
- `python -m orja` prints the wake phrase hint
- `hey slave time` shows current time
- `hey slave help` lists commands
- `hey slave timer 5 minutes` returns a placeholder timer response
- `data/orja.sqlite` and `logs/orja.log` appear after first run

