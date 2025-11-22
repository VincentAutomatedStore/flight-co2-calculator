import json
import os

def convert_airports_js_to_py():
    """Convert the frontend airports.js to a Python file"""
    
    # Path to your frontend airports.js
    frontend_airports_path = os.path.join('..', 'frontend', 'src', 'data', 'airports.js')
    
    # Path for the Python version
    backend_airports_path = os.path.join('shared_airports.py')
    
    try:
        with open(frontend_airports_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract the array from the JavaScript file
        if 'export const airports' in content:
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            if start_idx != -1 and end_idx != -1:
                array_content = content[start_idx:end_idx]
                
                # Create the Python file
                python_content = f'''"""
Shared airports data - auto-generated from frontend/airports.js
"""

airports = {array_content}
'''
                with open(backend_airports_path, 'w', encoding='utf-8') as f:
                    f.write(python_content)
                
                print(f"✅ Successfully converted {frontend_airports_path} to {backend_airports_path}")
                return True
                
    except Exception as e:
        print(f"❌ Error converting airports: {e}")
    
    return False

if __name__ == '__main__':
    convert_airports_js_to_py()