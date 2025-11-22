import json
import os
import re

def fix_airports_conversion_v2():
    """Properly convert JavaScript airports.js to Python format - handles trailing commas"""
    
    # Path to your frontend airports.js
    frontend_airports_path = os.path.join('..', 'frontend', 'src', 'data', 'airports.js')
    
    # Path for the Python version
    backend_airports_path = os.path.join('shared_airports.py')
    
    try:
        with open(frontend_airports_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📁 Original file size: {len(content)} characters")
        
        # Extract the array from the JavaScript file
        if 'export const airports' in content:
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            if start_idx != -1 and end_idx != -1:
                array_content = content[start_idx:end_idx]
                
                print("🔄 Converting JavaScript to valid JSON...")
                
                # Step 1: Add quotes around property names
                array_content = re.sub(r'(\w+):', r'"\1":', array_content)
                
                # Step 2: Remove trailing commas (commas before ] or })
                array_content = re.sub(r',\s*([}\]])', r'\1', array_content)
                
                # Step 3: Fix any remaining JavaScript syntax issues
                array_content = array_content.replace("'", '"')  # Single to double quotes
                
                # Step 4: Remove comments (just in case)
                array_content = re.sub(r'//.*$', '', array_content, flags=re.MULTILINE)
                
                print("🔍 Validating JSON conversion...")
                
                # Parse as JSON to validate
                try:
                    airports_data = json.loads(array_content)
                    print(f"✅ Successfully parsed {len(airports_data)} airports")
                    
                    # Create the Python file with proper syntax
                    python_content = f'''"""
Shared airports data - auto-generated from frontend/airports.js
"""

airports = {json.dumps(airports_data, indent=2, ensure_ascii=False)}
'''
                    with open(backend_airports_path, 'w', encoding='utf-8') as f:
                        f.write(python_content)
                    
                    print(f"✅ Successfully created {backend_airports_path}")
                    print(f"📊 Sample of first airport: {json.dumps(airports_data[0], indent=2)}")
                    return True
                    
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing error: {e}")
                    # Let's find the problematic line
                    lines = array_content.split('\n')
                    error_line = e.lineno if hasattr(e, 'lineno') else 'unknown'
                    error_col = e.colno if hasattr(e, 'colno') else 'unknown'
                    print(f"🔍 Error at line {error_line}, column {error_col}")
                    if error_line != 'unknown' and error_line < len(lines):
                        print(f"🔍 Problematic line: {lines[error_line-1]}")
                
    except Exception as e:
        print(f"❌ Error converting airports: {e}")
        import traceback
        print(f"🔍 Detailed error: {traceback.format_exc()}")
    
    return False

if __name__ == '__main__':
    fix_airports_conversion_v2()