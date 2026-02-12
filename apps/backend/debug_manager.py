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
    try:
        workflow = mgr.get_workflow("test character")
        print("Workflow loaded OK, nodes:", len(workflow))
    except Exception as e:
        print("Workflow error:", e)
        import traceback
        traceback.print_exc()

    print("Generating image...")
    result = mgr.generate_image(user_pos="test character")
    print("Result:", result)
else:
    print("ComfyUI not reachable")
