import sys
import os
import time
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from modules.characters.image_gen.manager import ImageGenManager

mgr = ImageGenManager()
prompt_id = "90e461ec-b7bf-4462-b06f-ef465c17d519"

print("Waiting for execution...")
time.sleep(2)

status = mgr.get_status(prompt_id)
print("Status:", status)

if status:
    print("History keys:", list(status.keys()))
    # Look for outputs
    if prompt_id in status:
        outputs = status[prompt_id].get("outputs", {})
        print("Outputs:", list(outputs.keys()))
        for node_id, output in outputs.items():
            if "images" in output:
                print(f"Node {node_id} has images:", output["images"])
else:
    print("No status returned")
