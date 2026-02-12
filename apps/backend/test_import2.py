import sys
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
print("Base dir:", BASE_DIR)
try:
    from modules.characters.image_gen.manager import ImageGenManager
    print("Import OK")
    mgr = ImageGenManager()
    print("Manager created")
    print("Connection:", mgr.check_comfyui_connection())
except Exception as e:
    import traceback
    traceback.print_exc()