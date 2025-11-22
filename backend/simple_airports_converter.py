import os

def simple_airports_converter():
    """Simple direct converter that just copies and fixes the syntax"""
    
    frontend_path = os.path.join('..', 'frontend', 'src', 'data', 'airports.js')
    backend_path = 'shared_airports.py'
    
    print("🔄 Simple direct conversion...")
    
    try:
        # Read the entire file
        with open(frontend_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        print(f"📁 Read {len(content)} characters")
        
        # Find the export line and extract just the array assignment
        if 'export const airports' in content:
            # Get everything after 'export const airports = '
            start_idx = content.find('export const airports = ')
            if start_idx != -1:
                # Start from after the assignment
                start_idx += len('export const airports = ')
                # Find the end (semicolon or end of file)
                end_idx = content.find(';', start_idx)
                if end_idx == -1:
                    end_idx = len(content)
                
                array_content = content[start_idx:end_idx].strip()
                print(f"📊 Extracted array content: {len(array_content)} characters")
                
                # Simple fixes for Python syntax
                # 1. Add quotes around property names
                array_content = array_content.replace('code:', '"code":')
                array_content = array_content.replace('name:', '"name":')
                array_content = array_content.replace('city:', '"city":')
                array_content = array_content.replace('country:', '"country":')
                array_content = array_content.replace('search:', '"search":')
                array_content = array_content.replace('latitude:', '"latitude":')
                array_content = array_content.replace('longitude:', '"longitude":')
                
                # 2. Write the Python file
                with open(backend_path, 'w', encoding='utf-8') as f:
                    f.write('"""\n')
                    f.write('Shared airports data\n')
                    f.write('"""\n\n')
                    f.write('airports = ')
                    f.write(array_content)
                
                print(f"✅ Created {backend_path}")
                print("📝 First 200 characters:")
                print(array_content[:200])
                return True
        
        print("❌ Could not find airports export")
        return False
        
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        return False

if __name__ == '__main__':
    simple_airports_converter()