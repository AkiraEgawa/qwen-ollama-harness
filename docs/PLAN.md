# Main sections
- AGENT.md (General setup rules of AGENT)
- agent.py (The code for the agent)
- main.py (Integration of agent.py into a user-friendly endpoint)
- requirements.txt (These are requirements, you need 'em)
- data/ (Add this folder to .gitignore to avoid the .claude issue)
    - MEMORY.md (short session notes)
    - sessions/ (has .jsonl transcripts per session ID)
- util/
    - __init__.py
    - settings.json (settings for the model such as temperature, model to run via ollama, etc)
    - memory.py (handles what things to store in memory.jsonl)
    - tools.py (the tools that are available to the agent)
    

Session Memory
- Figure out how to get a unique session id
- Call append_action from memory.py
- Do we load at start or load at end?
