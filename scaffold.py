import os
import re

plan_path = "/home/keshav-pi/.gemini/antigravity-cli/brain/f89ebbf4-98c1-4b9f-9f7b-4570e74d4d7a/timescope_implementation_plan.md"
workspace_root = "/storage/Repositories/TimesFM3"

with open(plan_path, 'r') as f:
    content = f.read()

# Pattern to find #### [NEW] `filepath` and the subsequent code block
pattern = re.compile(r'#### \[NEW\] `([^`]+)`.*?\n```[a-zA-Z]*\n(.*?)```', re.DOTALL)
matches = pattern.findall(content)

print(f"Found {len(matches)} files to create.")

for filepath, code in matches:
    filepath = filepath.strip()
    if filepath.endswith('/'):
        print(f"Skipping directory marker: {filepath}")
        continue
    
    abs_path = os.path.join(workspace_root, filepath)
    print(f"Writing {abs_path}...")
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, 'w') as f:
        f.write(code)

print("Done scaffolding.")
