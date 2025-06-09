import os
import json
import subprocess
import sys
from pathlib import Path

def main():
    print("Setting up Sequential Thinking MCP server...")

    # Create the directory for the MCP server
    mcp_dir = Path(os.path.expanduser("~")) / "OneDrive" / "Documents" / "Cline" / "MCP" / "sequentialthinking"
    os.makedirs(mcp_dir, exist_ok=True)
    print(f"Created directory: {mcp_dir}")

    # Path to the VSCode settings directory
    vscode_settings_dir = Path(os.environ.get('APPDATA')) / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings"
    settings_file = vscode_settings_dir / "cline_mcp_settings.json"
    
    print(f"Settings directory: {vscode_settings_dir}")
    print(f"Settings file: {settings_file}")
    
    # Create the settings directory if it doesn't exist
    os.makedirs(vscode_settings_dir, exist_ok=True)
    
    # Check if the settings file exists
    settings = {}
    if settings_file.exists():
        try:
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                print("Existing settings file found.")
        except json.JSONDecodeError:
            print("Error reading settings file. Creating a new one.")
    else:
        print("Settings file not found. Creating a new one.")
    
    # Make sure mcpServers exists
    if 'mcpServers' not in settings:
        settings['mcpServers'] = {}
    
    # Add our new server
    server_name = "github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking"
    
    settings['mcpServers'][server_name] = {
        "command": "npx",
        "args": [
            "-y",
            "@modelcontextprotocol/server-sequential-thinking"
        ],
        "disabled": False,
        "autoApprove": []
    }
    
    # Write the updated settings back to the file
    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=2)
    
    print(f"Updated settings file with Sequential Thinking MCP server configuration.")
    
    # Also create a local copy for reference
    with open("cline_mcp_settings.json", 'w') as f:
        json.dump(settings, f, indent=2)
    
    print("Local copy of settings file created.")
    
    # Try to install the MCP server package
    try:
        print("Installing Sequential Thinking MCP server...")
        subprocess.run(["npx", "-y", "@modelcontextprotocol/server-sequential-thinking", "--version"], 
                      capture_output=True, text=True, check=True)
        print("Sequential Thinking MCP server installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing MCP server: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
    
    print("\nSetup complete! Please restart VS Code to load the new MCP server.")
    print("After restarting, you can use the sequential_thinking tool.")

if __name__ == "__main__":
    main()
