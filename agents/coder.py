import json
import os
import requests
import sys

OLLAMA_BASE = "http://localhost:11434"
MODEL = "qwen3-coder-next:cloud"
WORKSPACE = "/home/inder/autoforge/workspace"

SYSTEM = """You are an expert Python developer.
Output ONLY a valid JSON object mapping filename to file content.
No explanation, no markdown fences, no prose. Just raw JSON like:
{"main.py": "...full content...", "models.py": "...full content..."}"""

def run() -> dict:
    # Read plan
    with open(f"{WORKSPACE}/plan.json") as f:
        plan = json.load(f)

    task_list = "\n".join(
        f"- {t['title']}: {t['description']}" for t in plan["tasks"]
    )

    prompt = f"""Write complete, working Python source files for this project.

Project: {plan['project']}

Tasks:
{task_list}

Return ONLY a JSON object where keys are filenames and values are complete file contents.
Include all necessary files to make the project fully functional."""

    with open(f"{WORKSPACE}/logs/coder.log", "a") as f:
        f.write(f"[CODER] Starting code generation for: {plan['project']}\n")

    response = requests.post(
        f"{OLLAMA_BASE}/api/generate",
        json={"model": MODEL, "prompt": prompt, "system": SYSTEM, "stream": False},
        timeout=300,
    )
    response.raise_for_status()
    raw = response.json()["response"].strip()

    # Strip markdown fences if model adds them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    files = json.loads(raw)

    # Write each file to workspace/src/
    os.makedirs(f"{WORKSPACE}/src", exist_ok=True)
    for filename, content in files.items():
        filepath = f"{WORKSPACE}/src/{filename}"
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            f.write(content)
        print(f"[CODER] Written: {filename}")

    with open(f"{WORKSPACE}/logs/coder.log", "a") as f:
        f.write(f"[CODER] Written {len(files)} files: {list(files.keys())}\n")

    with open(f"{WORKSPACE}/status.txt", "w") as f:
        f.write("CODER_DONE")

    print(f"[CODER] Done — {len(files)} files written to workspace/src/")
    return files

if __name__ == "__main__":
    run()
