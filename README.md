# Qwen Ollama Harness
This is an ai harness to turn any locally ran AI on ollama into an agent.
`main.py` is the frontend, it is not yet finished and isn't linked to the agent
`agent.py` is a bare bones agent running on qwen2.5-coder:7b

# Running
I haven't created the proper requirements.txt yet, so you'll have to install them by reading the top libraries
To try the agent, run:
```bash
python agent.py
```

# Inspiration
This project was inspired by a curiosity of how agents worked. Additionally, due to recent cyber security issues regarding AI, this agent is made to always be secure by running locally, avoiding possible leaks
