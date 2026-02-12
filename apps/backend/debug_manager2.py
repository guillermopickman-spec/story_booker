import sys
import os
import logging
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

logging.basicConfig(level=logging.DEBUG)

from modules.characters.image_gen.manager import ImageGenManager
from modules.characters.image_gen.workflow_composer import WorkflowComposer

# Find out which workflow is being used
composer = WorkflowComposer()
print("Workflow dir:", composer.workflow_dir)
print("Workflow name:", composer.workflow_name)
template = composer._load_template()
print("Template loaded. Keys:", list(template.keys())[:10])
# Print the template to see its structure
import json
print(json.dumps(template, indent=2)[:2000])
