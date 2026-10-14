# ColdMailr AI ✉️

**Zero-prompt cold emails for job seekers.** Enter a company, a role and one achievement. Get a ready-to-send cold email in one click. No "act as a career coach..." prompting needed.

🔗 **Live demo:** https://coldmailr.onrender.com/
*(Hosted on a free Render instance. The first load after idle time can take up to a minute.)*

Built for the Hacktoberfest Open-Source AI Challenge (Week 2: Side Hustle).

---

## Why not just use ChatGPT?

| Chat LLM | ColdMailr AI |
|---|---|
| You write "act as a recruiter..." every time | Role, rules and tone are built in. You only enter facts |
| Output format changes on every run | Same structure every time: subject, greeting, 3 short paragraphs, one low-pressure ask |
| May invent numbers or company news | A validator rejects invented numbers and unsupported claims |
| One answer, take it or leave it | The model writes 3 candidates, the app picks the cleanest |
| You judge the quality | Cliché phrases and length limits are enforced in code |

A skilled prompter can get a similar email from any chat model. ColdMailr packages that expertise so nobody has to prompt, and checks the output before the user sees it.

## How it works

```
Browser (UI + progress bar)
   │  POST /api/generate-cold-email
   ▼
Node.js + Express (server.js)
   │  spawns Python, sends JSON over stdin
   ▼
tinker_generator.py
   ├─ builds a chat prompt: strict system rules + 4 few-shot examples
   ├─ samples 3 candidates from Qwen3-8B via Tinker
   ├─ validates each (format, length, company mentioned,
   │   banned phrases, no invented numbers)
   └─ returns the best candidate
```

- **Model:** [Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B) (open-weight), sampled through [Tinker](https://thinkingmachines.ai/tinker/).
- **Honest failures:** if generation fails, the user sees an error. A fake template is never shown as AI output.

## Project structure

```
server.js            Express server, UI, and the Python bridge
tinker_generator.py  Prompt, Tinker sampling, validator
check.py             Step-by-step health check for the Python side
requirements.txt     Python dependencies
package.json         Node dependencies
LICENSE              MIT
```

## Run locally

**Requirements:** Node.js 18+, Python 3.11+, a Tinker API key.

**1. Clone and install Node dependencies**

```bash
git clone https://github.com/Abbas7120/ColdMailR.git
cd ColdMailR
npm install
```

**2. Create the Python environment**

Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

macOS / Linux:
```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

> On Windows, if `python` opens the Microsoft Store, install Python from python.org (tick "Add to PATH") and turn off the `python.exe` entries under *Settings > Apps > Advanced app settings > App execution aliases*.

**3. Add your environment variables**

Create a `.env` file in the project root:

```
PORT=3000
TINKER_API_KEY=your_key_here
```

**4. Check the Python side (recommended)**

```bash
# Windows
.venv\Scripts\python.exe check.py
# macOS / Linux
.venv/bin/python check.py
```

Every line should say `[PASS]`. A `[FAIL]` names the exact step that broke.

**5. Start the app**

```bash
node server.js
```

Open http://localhost:3000.

> The `PyTorch was not found` warning from `transformers` is harmless. Only the tokenizer is used.

## Deploy on Render (no Docker)

1. Push the repo to GitHub. Do **not** commit `.env` or `.venv` (they are in `.gitignore`).
2. On Render: **New + > Web Service**, select the repo, runtime **Node**.
3. **Build command:**
   ```
   python3 --version && npm install && python3 -m venv .venv && .venv/bin/pip install --no-cache-dir -r requirements.txt && .venv/bin/python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('Qwen/Qwen3-8B')"
   ```
4. **Start command:** `node server.js`
5. **Environment variables:** `TINKER_API_KEY` (your key) and `HF_HOME` = `/opt/render/project/src/.hf`
6. If the build shows Python older than 3.11, add `PYTHON_VERSION` = `3.12.3`.

The free tier has 512 MB RAM. If the app runs out of memory, use a paid instance.

## Customizing

- **Model:** change `MODEL` in `tinker_generator.py` to another model supported by Tinker.
- **Tone and rules:** edit `SYSTEM_PROMPT` and the `EXAMPLES` list.
- **Quality checks:** edit `BANNED` and the `issues()` function.
- **Candidates per request:** change `NUM_CANDIDATES`.

## Known limitations

- Each request starts a Python process and loads the tokenizer, which adds a few seconds. A persistent Python service (for example FastAPI) would be faster.
- No rate limiting or user accounts yet, so a public deployment can use up your Tinker credit.
- Output quality depends on the achievement you enter. Specific, measurable achievements produce the best emails.
- The sign-off uses a `[Your Name]` placeholder for the user to replace.

## Roadmap

- [ ] Sender name field (no placeholders left to fill)
- [ ] Tone selector (formal, friendly, direct)
- [ ] Follow-up email generator
- [ ] Rate limiting and user accounts
- [ ] Fine-tune a model on high-performing cold emails
- [ ] Persistent Python service for faster responses


## License
SYED MOHAMMAD ABBAS RIZVI
[MIT](LICENSE)
