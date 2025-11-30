import os
import httpx
import base64
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "vikashegde21"
REPO_NAME = "MCP-A2A-github_actions"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

mcp = FastMCP("DevOps Pipeline Server")

@mcp.tool()
def list_workflows() -> str:
    """Lists all GitHub Action workflows. Returns 'No workflows found' if empty."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows"
    try:
        with httpx.Client() as client:
            resp = client.get(url, headers=HEADERS)
            if resp.status_code == 404: return "Repository not found."
            resp.raise_for_status()
            data = resp.json()
            
            count = data.get("total_count", 0)
            if count == 0:
                return "No workflows found. The repository has no active pipelines."
                
            workflows = [f"ID: {w['id']} | Name: {w['name']} | State: {w['state']}" for w in data.get('workflows', [])]
            return "\n".join(workflows)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def create_basic_pipeline() -> str:
    """Creates a simple 'Hello World' CI pipeline with a unique name."""
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"workflow_{timestamp}.yml"
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/.github/workflows/{filename}"
    
    content = f"""
name: CI Pipeline {timestamp}
on: [workflow_dispatch]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Run a one-line script
        run: echo "Hello, world! Pipeline {timestamp} is working."
    """
    
    encoded_content = base64.b64encode(content.encode()).decode()
    
    payload = {
        "message": f"Create pipeline {filename} via MCP Agent",
        "content": encoded_content
    }
    
    try:
        with httpx.Client() as client:
            resp = client.put(url, json=payload, headers=HEADERS)
            if resp.status_code == 201:
                local_path = os.path.join(".github", "workflows", filename)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with open(local_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return f"SUCCESS: Created new pipeline '.github/workflows/{filename}' (local copy saved)"
            return f"FAILED: {resp.status_code} - {resp.text}"
    except Exception as e:
        return f"Error creating pipeline: {str(e)}"

if __name__ == "__main__":
    mcp.run()