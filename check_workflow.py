from modules.characters.image_gen.workflow_composer import WorkflowComposer
import os

# Initialize workflow composer
composer = WorkflowComposer()

try:
    # Try to load the default workflow
    template = composer._load_template()
    print('✅ Default workflow loaded successfully')
    print('Template path:', composer.loaded_template_path)
    
    # Check if it contains the right nodes for character generation
    print('\n📋 Workflow nodes:')
    for node_id, node_data in template.items():
        class_type = node_data.get('class_type', 'Unknown')
        if 'text' in node_data.get('inputs', {}):
            text = node_data['inputs']['text']
            print(f'  {node_id}: {class_type} - "{text[:50]}..."')
        else:
            print(f'  {node_id}: {class_type}')
            
    # Check if we can compose a workflow with a test prompt
    print('\n🧪 Testing workflow composition with test prompt:')
    test_workflow = composer.compose(
        user_pos="a cute baby fox with big eyes and fluffy tail",
        user_neg="text, watermark, blurry, low quality"
    )
    
    print('✅ Workflow composed successfully')
    print('Composed nodes with text:')
    for node_id, node_data in test_workflow.items():
        class_type = node_data.get('class_type', 'Unknown')
        if 'text' in node_data.get('inputs', {}):
            text = node_data['inputs']['text']
            print(f'  {node_id}: {class_type} - "{text[:80]}..."')
    
except Exception as e:
    print('❌ Error:', e)
    import traceback
    traceback.print_exc()