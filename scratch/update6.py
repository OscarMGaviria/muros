import os

file_path = r'frontend/src/components/ParametersForm.vue'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the ^\circ issue
content = content.replace("^\circ", "^\\\\circ")

# Expand the modal width
content = content.replace(
    'class="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden flex flex-col max-h-[90vh]"', 
    'class="bg-white rounded-xl shadow-2xl w-full max-w-3xl overflow-hidden flex flex-col max-h-[90vh]"'
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated width and escapes successfully")
