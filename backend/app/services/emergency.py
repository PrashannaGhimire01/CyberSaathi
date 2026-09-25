import json
from pathlib import Path

GUIDE_PATH = Path(__file__).parent.parent / "rules" / "emergency.json"

with open(GUIDE_PATH, encoding="utf-8") as f:
    GUIDE = json.load(f)

def build_emergency_plan(shared, language):
    plan = GUIDE["plan"]
    step_ids = list(plan["first"])
    for situation in plan["priority"]:
        if situation in shared:
            step_ids.extend(plan[situation])
    step_ids.extend(plan["last"])
    unique_ids = list(dict.fromkeys(step_ids))
    return [GUIDE["steps"][step_id][language] for step_id in unique_ids]