import os
import sys
import subprocess
from dotenv import load_dotenv

def main():
    # Load environment variables from .env file
    # Assuming .env is in the project root (one level up from scripts)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dotenv_path = os.path.join(project_root, '.env')
    
    if os.path.exists(dotenv_path):
        print(f"Loading .env from {dotenv_path}")
        load_dotenv(dotenv_path)
    else:
        print(f"Warning: .env file not found at {dotenv_path}")

    # Map NEO4J_USER to NEO4J_USERNAME if needed
    if 'NEO4J_USER' in os.environ and 'NEO4J_USERNAME' not in os.environ:
        os.environ['NEO4J_USERNAME'] = os.environ['NEO4J_USER']

    # Path to the mcp-neo4j-cypher executable
    # It should be in the same venv as this script is running from
    executable = "mcp-neo4j-cypher"
    
    # On Windows, we might need the full path if it's not in PATH
    # But if we run this script with the venv python, the venv scripts should be in PATH or accessible
    # Let's try to find it in the venv scripts dir
    venv_scripts = os.path.dirname(sys.executable)
    executable_path = os.path.join(venv_scripts, "mcp-neo4j-cypher.exe")
    
    if not os.path.exists(executable_path):
        # Fallback to just the command name if not found in expected location
        executable_path = executable

    print(f"Starting Neo4j MCP Server using {executable_path}...")
    
    # Pass all arguments to the underlying command
    args = [executable_path] + sys.argv[1:]
    
    try:
        # Run the process
        subprocess.run(args, env=os.environ, check=True)
    except KeyboardInterrupt:
        print("\nStopping Neo4j MCP Server.")
    except subprocess.CalledProcessError as e:
        print(f"Error running Neo4j MCP Server: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
