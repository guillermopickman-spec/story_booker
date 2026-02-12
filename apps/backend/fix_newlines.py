with open('main_app.py', 'r', encoding='utf-8') as f:
    content = f.read()
new_content = content.replace('\\n', '\n')
with open('main_app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
print('Fixed newlines')