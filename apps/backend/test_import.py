import sys
sys.path.append(r'C:\Users\Guill\Documents\OpenClaw\story-booker\apps\backend')
try:
    from modules.characters.image_gen.manager import ImageGenManager
    print("Import OK")
    mgr = ImageGenManager()
    print("Manager created")
    print("Connection:", mgr.check_comfyui_connection())
except Exception as e:
    import traceback
    traceback.print_exc()