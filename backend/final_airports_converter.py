import os
import re

def final_airports_converter():
    """Final converter that creates valid Python syntax"""
    
    frontend_path = os.path.join('..', 'frontend', 'src', 'data', 'airports.js')
    backend_path = 'shared_airports.py'
    
    print("🔄 Creating valid Python syntax...")
    
    try:
        # Read the file
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
        
        # Convert line by line to ensure valid Python
        lines = js_array.split('\n')
        python_lines = ['[']  # Start with opening bracket
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('{') and line.endswith('}'):
                # This is an object line - convert it and add comma
                python_line = convert_js_object_to_python(line)
                # Add comma unless it's the last object before closing bracket
                if i < len(lines) - 2:  # Not the last object
                    python_line += ','
                python_lines.append('  ' + python_line)
            elif line == '[' or line == ']':
                # Keep the brackets
                python_lines.append(line)
            elif line.endswith(','):
                # This might be a line with just a comma
                continue  # We'll handle commas ourselves
        
        python_lines.append(']')  # Closing bracket
        
        # Write the Python file
        with open(backend_path, 'w', encoding='utf-8') as f:
            f.write('"""\n')
            f.write('Shared airports data - converted from frontend/airports.js\n')
            f.write('"""\n\n')
            f.write('airports = \\\n')
            f.write('\n'.join(python_lines))
        
        print(f"✅ Successfully created {backend_path}")
        print("📝 Sample of converted syntax:")
        print('\n'.join(python_lines[:5]))  # Show first few lines
        return True
        
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        import traceback
        print(f"🔍 Detailed error: {traceback.format_exc()}")
        return False

def convert_js_object_to_python(js_line):
    """Convert a single JavaScript object line to Python dictionary syntax"""
    # Remove trailing commas and whitespace
    line = js_line.strip().rstrip(',')
    
    # Convert property names to quoted strings
    line = re.sub(r'(\w+):', r'"\1":', line)
    
    # Ensure proper quotes
    line = line.replace("'", '"')
    
    return line

if __name__ == '__main__':
    final_airports_converter()