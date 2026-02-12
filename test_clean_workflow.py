from modules.characters.image_gen.workflow_composer import WorkflowComposer
import os

# Test with the clean workflow (no RMBG)
clean_workflow_path = "./workflows/character_creator_no_rmbg.json"

print(f"Testing with clean workflow: {clean_workflow_path}")

# Initialize workflow composer with clean workflow
composer = WorkflowComposer(template_path=clean_workflow_path)

try:
    # Load the clean workflow
    template = composer._load_template()
    print('Clean workflow loaded successfully')
    print('Template path:', composer.loaded_template_path)
    
    # Check workflow nodes
    print('Clean workflow nodes:')
    for node_id, node_data in template.items():
        class_type = node_data.get('class_type', 'Unknown')
        if 'text' in node_data.get('inputs', {}):
            text = node_data['inputs']['text']
            print(f'  {node_id}: {class_type} - "{text[:50]}..."')
        else:
            print(f'  {node_id}: {class_type}')
    
    # Check if RMBG node is missing
    has_rmbg = any(node.get('class_type') == 'RMBG' for node in template.values())
    print(f'Has RMBG node: {has_rmbg}')
            
    # Test workflow composition with cute baby fox prompt
    print('Testing workflow composition with cute baby fox prompt:')
    test_workflow = composer.compose(
        user_pos="a cute baby fox with big eyes and fluffy tail",
        user_neg="text, watermark, blurry, low quality"
    )
    
    print('Workflow composed successfully')
    print('Composed nodes with text:')
    for node_id, node_data in test_workflow.items():
        class_type = node_data.get('class_type', 'Unknown')
        if 'text' in node_data.get('inputs', {}):
            text = node_data['inputs']['text']
            print(f'  {node_id}: {class_type} - "{text[:80]}..."')
    
    # Test image generation
    print('Testing image generation...')
    from modules.characters.image_gen.manager import ImageGenManager
    
    # Initialize with clean workflow
    manager = ImageGenManager()
    
    # Override the workflow path
    manager.composer = WorkflowComposer(template_path=clean_workflow_path)
    
    print('Generating cute baby fox character...')
    response = manager.generate_image("a cute baby fox with big eyes and fluffy tail", "text, watermark, blurry, low quality")
    
    if response:
        prompt_id = response.get('prompt_id')
        print(f'Image generation started! Prompt ID: {prompt_id}')
        print('This should work without RMBG errors now!')
    else:
        print('Failed to start image generation')
    
except Exception as e:
    print('Error:', e)
    import traceback
    traceback.print_exc()