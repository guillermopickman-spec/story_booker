import sys
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from modules.characters.image_gen.manager import ImageGenManager

mgr = ImageGenManager()
print("Checking connection...")
conn = mgr.check_comfyui_connection()
print("Connection:", conn)

if conn:
    print("Getting workflow...")
    workflow = mgr.get_workflow("test character")
    print("Workflow loaded OK, nodes:", len(workflow))

    # Print the full workflow to inspect
    import json
    print("Workflow JSON:")
    print(json.dumps(workflow, indent=2)[:3000])

    print("\nGenerating image...")
    result = mgr.generate_image(user_pos="test character")
    print("Result:", result)
else:
    print("ComfyUI not reachable")
