import json
import requests
import sys

OLLAMA_BASE = "http://localhost:11434"
MODEL = "kimi-k2.5:cloud"
WORKSPACE = "/home/inder/autoforge/workspace"

SYSTEM = """You are a project planner. Output ONLY valid JSON, nothing else.
No markdown, no explanation, no code blocks. Just raw JSON."""

def run(project_description: str) -> dict:
    prompt = f"""Break this project into 4-6 tasks. Return ONLY this JSON structure:
{{
  "project": "<one line summary>",
  "tasks": [
    {{"id": "t1", "title": "<title>", "description": "<what to build>", "depends_on": []}},
    {{"id": "t2", "title": "<title>", "description": "<what to build>", "depends_on": ["t1"]}}
  ]
}}

Project: {project_description}"""

    response = requests.post(
        f"{OLLAMA_BASE}/api/generate",
        json={"model": MODEL, "prompt": prompt, "system": SYSTEM, "stream": False},
        timeout=120,
    )
    response.raise_for_status()
    raw = response.json()["response"].strip()

    # Strip markdown fences if model adds them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    plan = json.loads(raw)

    # Write outputs
    with open(f"{WORKSPACE}/plan.json", "w") as f:
        json.dump(plan, f, indent=2)

    with open(f"{WORKSPACE}/logs/planner.log", "a") as f:
        f.write(f"[PLANNER] Plan written with {len(plan['tasks'])} tasks for: {plan['project']}\n")

    with open(f"{WORKSPACE}/status.txt", "w") as f:
        f.write("PLANNER_DONE")

    print(f"[PLANNER] Done — {len(plan['tasks'])} tasks written to workspace/plan.json")
    return plan

if __name__ == "__main__":
    desc = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("Project description: ")
    run(desc)
