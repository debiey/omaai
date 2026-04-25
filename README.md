# OmaAI 🤖

**Your AI-powered Linux companion — built for developers, sysadmins, and learners.**

OmaAI runs entirely from your terminal, powered by a local Ollama model. No internet required, no API keys, no cloud.

---

## ✨ Commands

| Command | What it does |
|---------|-------------|
| `oma explain <topic>` | Explain any Linux command or error |
| `oma fix <command>` | Suggest a fix for a broken command |
| `oma monitor` | Show real-time CPU, RAM, and disk stats |
| `oma teach` | Interactive Linux lessons and quizzes |

---

## ⚡ Quick Install

**1. Install Ollama** (if you haven't already)
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull tinyllama
ollama serve
```

**2. Install OmaAI**
```bash
git clone https://github.com/debiey/omaai.git
cd omaai
pip install -e .
```

**3. Run it**
```bash
oma explain "chmod 755"
oma fix "sudo apt-get udate"
oma monitor
oma teach
```

---

## 🎯 Examples

```bash
# Explain a command
oma explain "what does grep -r do"

# Fix a typo or failed command
oma fix "systemctl satrt nginx"

# Check system health
oma monitor

# Start a Linux lesson
oma teach
oma teach --lesson 3
oma teach --progress
```

---

## 🗂️ Project Structure

```
omaai/
├── src/
│   └── omaai/
│       ├── ai.py              # Ollama AI engine
│       ├── main.py            # CLI entry point
│       └── commands/
│           ├── explain.py     # oma explain
│           ├── fix.py         # oma fix
│           ├── monitor.py     # oma monitor
│           └── teach.py       # oma teach
├── pyproject.toml
└── README.md
```

---

## 🔧 Requirements

- Python 3.10+
- [Ollama](https://ollama.com) running locally
- tinyllama model (or any other Ollama model)

To use a different model, edit `src/omaai/ai.py` and change `DEFAULT_MODEL`.

---

## 👤 Author

**Chioma Obiagboso** — Linux Systems Engineer · AI Tools Developer · RHCSA Certified

[GitHub](https://github.com/debiey) · [Mimir](https://github.com/debiey/mimir)

---

## 📜 License

MIT
