#!/usr/bin/env python3
"""
Blueprint Route Analyzer for Data Analyzer

This script analyzes the legacy blueprints in the modules/routes/ directory
and documents their routes, methods, dependencies, and other important information.
The output is a detailed markdown report that can be used as a reference during
the migration process.

Usage:
    python blueprint_analyzer.py [--output report.md]
"""

import os
import sys
import inspect
import importlib.util
import re
from collections import defaultdict
import argparse
from typing import Dict, List, Tuple, Set, Optional


def load_module_from_path(module_path: str) -> Optional[object]:
    """
    Load a Python module from its file path.
    
    Args:
        module_path: Path to the module file
        
    Returns:
        The loaded module or None if loading failed
    """
    try:
        module_name = os.path.basename(module_path).replace('.py', '')
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        return None
    except Exception as e:
        print(f"Error loading module {module_path}: {e}")
        return None


def find_all_blueprint_files() -> List[str]:
    """
    Find all blueprint files in the modules/routes directory.
    
    Returns:
        List of file paths to blueprint modules
    """
    result = []
    routes_dir = 'modules/routes'
    
    if not os.path.exists(routes_dir):
        print(f"Error: {routes_dir} directory not found")
        return result
        
    for filename in os.listdir(routes_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            result.append(os.path.join(routes_dir, filename))
            
    return result


def extract_blueprint_name(module) -> str:
    """
    Extract the blueprint name from a module.
    
    Args:
        module: The loaded module
        
    Returns:
        The name of the blueprint
    """
    for name, obj in inspect.getmembers(module):
        if name.endswith('_bp'):
            return name
    return "unknown_blueprint"


def extract_routes(module, blueprint_name: str) -> List[Dict]:
    """
    Extract all routes defined for a blueprint in a module.
    
    Args:
        module: The loaded module
        blueprint_name: Name of the blueprint to look for
        
    Returns:
        List of dictionaries with route information
    """
    routes = []
    
    for name, func in inspect.getmembers(module, inspect.isfunction):
        source = inspect.getsource(func)
        
        # Look for route decorators
        route_matches = re.finditer(r'@{}\s*\.\s*route\s*\(\s*[\'"]([^\'"]*)[\'"](?:,\s*methods=\[([^\]]*)\])?\s*\)'.format(blueprint_name), source)
        
        for match in route_matches:
            route_path = match.group(1)
            methods_str = match.group(2)
            
            methods = []
            if methods_str:
                # Extract methods from the methods list
                methods = [m.strip(' \'"') for m in methods_str.split(',')]
            else:
                methods = ['GET']  # Default method is GET
                
            # Check if the route has login_required
            login_required = '@login_required' in source
            
            # Extract docstring if available
            docstring = inspect.getdoc(func) or "No description available"
            
            # Get the first paragraph of the docstring
            description = docstring.split('\n\n')[0].replace('\n', ' ').strip()
            
            routes.append({
                'name': name,
                'path': route_path,
                'methods': methods,
                'login_required': login_required,
                'description': description,
                'source': source
            })
            
    return routes


def extract_dependencies(module_source: str) -> Set[str]:
    """
    Extract import dependencies from a module's source code.
    
    Args:
        module_source: The source code of the module
        
    Returns:
        Set of imported module names
    """
    dependencies = set()
    
    # Match import statements
    import_patterns = [
        r'^\s*import\s+([a-zA-Z0-9_.,\s]+)',  # import x, y, z
        r'^\s*from\s+([a-zA-Z0-9_.]+)\s+import',  # from x import y
    ]
    
    for pattern in import_patterns:
        for match in re.finditer(pattern, module_source, re.MULTILINE):
            modules = match.group(1).split(',')
            for module in modules:
                # Get the base module name (e.g., 'os.path' -> 'os')
                base_module = module.strip().split('.')[0]
                if base_module and not base_module.startswith('_'):
                    dependencies.add(base_module)
    
    return dependencies


def extract_templates(module_source: str) -> Set[str]:
    """
    Extract template references from a module's source code.
    
    Args:
        module_source: The source code of the module
        
    Returns:
        Set of template names
    """
    templates = set()
    
    # Match render_template calls
    pattern = r'render_template\s*\(\s*[\'"]([^\'"]+)[\'"]'
    
    for match in re.finditer(pattern, module_source):
        template_name = match.group(1)
        templates.add(template_name)
    
    return templates


def analyze_blueprint(blueprint_path: str) -> Dict:
    """
    Analyze a blueprint file and extract all relevant information.
    
    Args:
        blueprint_path: Path to the blueprint module
        
    Returns:
        Dictionary with blueprint information
    """
    module = load_module_from_path(blueprint_path)
    if not module:
        return {
            'name': os.path.basename(blueprint_path),
            'error': 'Failed to load module'
        }
    
    # Read the entire file content
    with open(blueprint_path, 'r') as f:
        file_content = f.read()
    
    blueprint_name = extract_blueprint_name(module)
    routes = extract_routes(module, blueprint_name)
    dependencies = extract_dependencies(file_content)
    templates = extract_templates(file_content)
    
    return {
        'name': blueprint_name,
        'file': blueprint_path,
        'routes': routes,
        'dependencies': dependencies,
        'templates': templates,
        'module': module,
        'file_content': file_content
    }


def generate_report(blueprints: List[Dict], output_file: str) -> None:
    """
    Generate a markdown report from the blueprint analysis.
    
    Args:
        blueprints: List of blueprint information dictionaries
        output_file: Path to the output markdown file
    """
    with open(output_file, 'w') as f:
        f.write("# Blueprint Analysis Report\n\n")
        f.write("This report analyzes the legacy blueprints in the modules/routes/ directory ")
        f.write("and documents their routes, methods, dependencies, and other important information.\n\n")
        
        f.write("## Overview\n\n")
        f.write("| Blueprint | File | Routes | Templates | Dependencies |\n")
        f.write("|-----------|------|--------|-----------|--------------|\n")
        
        for bp in blueprints:
            f.write(f"| {bp['name']} | {bp['file']} | {len(bp['routes'])} | {len(bp['templates'])} | {len(bp['dependencies'])} |\n")
        
        f.write("\n## Detailed Analysis\n\n")
        
        for bp in blueprints:
            f.write(f"### {bp['name']}\n\n")
            f.write(f"**File:** {bp['file']}\n\n")
            
            f.write("#### Routes\n\n")
            f.write("| Function | Path | Methods | Login Required | Description |\n")
            f.write("|----------|------|---------|----------------|-------------|\n")
            
            for route in bp['routes']:
                methods = ', '.join(route['methods'])
                login_required = '✓' if route['login_required'] else '✗'
                
                # Truncate description if it's too long
                description = route['description']
                if len(description) > 100:
                    description = description[:97] + '...'
                
                f.write(f"| {route['name']} | {route['path']} | {methods} | {login_required} | {description} |\n")
            
            f.write("\n#### Dependencies\n\n")
            if bp['dependencies']:
                for dep in sorted(bp['dependencies']):
                    f.write(f"- {dep}\n")
            else:
                f.write("No dependencies found.\n")
            
            f.write("\n#### Templates\n\n")
            if bp['templates']:
                for template in sorted(bp['templates']):
                    f.write(f"- {template}\n")
            else:
                f.write("No templates found.\n")
            
            f.write("\n")
    
    print(f"Report generated: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze Flask blueprints in the modules/routes directory')
    parser.add_argument('--output', default='blueprint_analysis_report.md',
                        help='Output markdown file (default: blueprint_analysis_report.md)')
    
    args = parser.parse_args()
    
    print("=== Blueprint Route Analyzer ===")
    
    # Find all blueprint files
    blueprint_files = find_all_blueprint_files()
    
    if not blueprint_files:
        print("No blueprint files found in modules/routes directory")
        sys.exit(1)
    
    print(f"Found {len(blueprint_files)} blueprint files")
    
    # Analyze each blueprint
    blueprint_data = []
    for bp_file in blueprint_files:
        print(f"Analyzing {bp_file}...")
        blueprint_info = analyze_blueprint(bp_file)
        blueprint_data.append(blueprint_info)
    
    # Generate the report
    generate_report(blueprint_data, args.output)
    
    print("=== Analysis complete ===")
