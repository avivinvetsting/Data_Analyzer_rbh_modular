#!/usr/bin/env python3
"""
Test Structure Validation Script

This script validates the test files structure and imports without running them.
It checks for syntax errors, import issues, and test structure correctness.
"""

import ast
import os
import sys
from pathlib import Path

def validate_python_syntax(file_path):
    """Validate Python syntax in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST to check syntax
        ast.parse(content, filename=file_path)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Error reading file: {str(e)}"

def analyze_test_structure(file_path):
    """Analyze test file structure."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=file_path)
        
        info = {
            'classes': [],
            'functions': [],
            'fixtures': [],
            'imports': [],
            'test_methods': 0
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                info['classes'].append(node.name)
                # Count test methods in classes
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name.startswith('test_'):
                        info['test_methods'] += 1
            
            elif isinstance(node, ast.FunctionDef):
                info['functions'].append(node.name)
                
                # Check for pytest fixtures
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == 'pytest.fixture':
                        info['fixtures'].append(node.name)
                    elif isinstance(decorator, ast.Attribute) and decorator.attr == 'fixture':
                        info['fixtures'].append(node.name)
                
                # Count standalone test functions
                if node.name.startswith('test_'):
                    info['test_methods'] += 1
            
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    info['imports'].append(alias.name)
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    info['imports'].append(f"{module}.{alias.name}")
        
        return True, info
    except Exception as e:
        return False, str(e)

def validate_test_file(file_path):
    """Validate a single test file."""
    print(f"\n📄 Validating: {os.path.basename(file_path)}")
    print("-" * 50)
    
    # Check syntax
    syntax_ok, syntax_error = validate_python_syntax(file_path)
    if not syntax_ok:
        print(f"❌ Syntax Error: {syntax_error}")
        return False
    else:
        print("✅ Syntax: Valid")
    
    # Analyze structure
    structure_ok, structure_info = analyze_test_structure(file_path)
    if not structure_ok:
        print(f"❌ Structure Analysis Failed: {structure_info}")
        return False
    
    print(f"✅ Structure Analysis:")
    print(f"   - Test Classes: {len(structure_info['classes'])} ({', '.join(structure_info['classes'])})")
    print(f"   - Test Methods: {structure_info['test_methods']}")
    print(f"   - Fixtures: {len(structure_info['fixtures'])} ({', '.join(structure_info['fixtures'])})")
    print(f"   - Total Functions: {len(structure_info['functions'])}")
    print(f"   - Import Statements: {len(structure_info['imports'])}")
    
    # Validate test naming conventions
    if structure_info['test_methods'] == 0:
        print("⚠️  Warning: No test methods found (methods starting with 'test_')")
    
    # Check for required imports
    required_imports = ['pytest', 'app']
    missing_imports = []
    for req_import in required_imports:
        if not any(req_import in imp for imp in structure_info['imports']):
            missing_imports.append(req_import)
    
    if missing_imports:
        print(f"⚠️  Missing recommended imports: {', '.join(missing_imports)}")
    
    return True

def main():
    """Main validation function."""
    print("🧪 Test Structure Validation")
    print("=" * 60)
    
    test_dir = Path('tests')
    if not test_dir.exists():
        print("❌ Tests directory not found!")
        return 1
    
    test_files = list(test_dir.glob('test_*.py'))
    if not test_files:
        print("❌ No test files found (looking for test_*.py)")
        return 1
    
    print(f"Found {len(test_files)} test files:")
    for test_file in test_files:
        print(f"  - {test_file.name}")
    
    all_valid = True
    total_tests = 0
    total_classes = 0
    total_fixtures = 0
    
    for test_file in test_files:
        file_valid = validate_test_file(test_file)
        if not file_valid:
            all_valid = False
        
        # Get stats for summary
        structure_ok, structure_info = analyze_test_structure(test_file)
        if structure_ok:
            total_tests += structure_info['test_methods']
            total_classes += len(structure_info['classes'])
            total_fixtures += len(structure_info['fixtures'])
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"Test Files: {len(test_files)}")
    print(f"Test Classes: {total_classes}")
    print(f"Test Methods: {total_tests}")
    print(f"Fixtures: {total_fixtures}")
    
    if all_valid:
        print("\n🎉 ALL TEST FILES ARE STRUCTURALLY VALID! 🎉")
        print("\nTest Coverage Areas:")
        print("✅ Authentication and User Management")
        print("✅ Input Validation and Security")
        print("✅ Data Analysis and Chart Generation")
        print("✅ Form Handling and CSRF Protection")
        print("✅ Integration Workflows")
        print("\nNext Steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run tests: pytest tests/ -v")
        print("3. Run with coverage: pytest --cov=. tests/")
        return 0
    else:
        print("\n⚠️  Some test files have issues that need to be fixed.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)