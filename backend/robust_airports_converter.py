import os
import re

def robust_airports_converter():
    """Robust conversion that handles encoding and syntax issues"""
    
    frontend_path = os.path.join('..', 'frontend', 'src', 'data', 'airports.js')
    backend_path = 'shared_airports.py'
    
    print("🔄 Starting robust airports conversion...")
    
    try:
        # Read with proper encoding handling
        with open(frontend_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        print(f"📁 Read {len(content)} characters")
        
        # Find the array content
        start = content.find('[')
        end = content.rfind(']') + 1
        
        if start == -1 or end == -1:
            print("❌ Could not find array boundaries")
            return False
        
        js_array = content[start:end]
        print(f"📊 Extracted array of {len(js_array)} characters")
        
        # Convert JavaScript objects to Python dictionaries line by line
        lines = js_array.split('\n')
        python_lines = []
        
        for i, line in enumerate(lines):
            if '{' in line and '}' in line:
                # This is an object line - convert it
                python_line = convert_js_object_to_python(line)
                python_lines.append(python_line)
            else:
                # Keep other lines as-is (commas, brackets)
                python_lines.append(line)
        
        # Rebuild the content
        python_array = '\n'.join(python_lines)
        
        # Write the Python file
        with open(backend_path, 'w', encoding='utf-8') as f:
            f.write('"""\n')
            f.write('Shared airports data - converted from frontend/airports.js\n')
            f.write('"""\n\n')
            f.write('airports = ')
            f.write(python_array)
        
        print(f"✅ Successfully created {backend_path}")
        return True
        
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        return False

def convert_js_object_to_python(js_line):
    """Convert a single JavaScript object line to Python dictionary syntax"""
    # Remove trailing commas
    line = js_line.rstrip().rstrip(',')
    
    # Convert property names to quoted strings
    line = re.sub(r'(\w+):', r'"\1":', line)
    
    # Ensure proper quotes
    line = line.replace("'", '"')
    
    return line

if __name__ == '__main__':
    robust_airports_converter()