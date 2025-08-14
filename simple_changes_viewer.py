"""
Simple Changes Viewer - Standalone Version
A simple web interface to view Git changes without complex dependencies
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
import subprocess
import json
from datetime import datetime
from typing import List, Dict, Optional
import uvicorn

app = FastAPI(
    title="Simple Changes Viewer",
    description="View Git changes in your trading strategies",
    version="1.0.0"
)

# Set up templates
templates = Jinja2Templates(directory="templates")

class SimpleChangesViewer:
    """Handles Git operations and change tracking"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
    
    def get_git_status(self) -> Dict:
        """Get current Git status"""
        try:
            # Check if Git is available
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )
            
            if result.returncode != 0:
                return {"error": "Git not available or not a repository"}
            
            # Parse git status
            status_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            changes = {
                "modified": [],
                "added": [],
                "deleted": [],
                "untracked": []
            }
            
            for line in status_lines:
                if line:
                    status = line[:2]
                    filename = line[3:]
                    
                    if status == "M ":
                        changes["modified"].append(filename)
                    elif status == "A ":
                        changes["added"].append(filename)
                    elif status == "D ":
                        changes["deleted"].append(filename)
                    elif status == "??":
                        changes["untracked"].append(filename)
            
            return changes
            
        except Exception as e:
            return {"error": f"Error getting Git status: {str(e)}"}
    
    def get_file_diff(self, filename: str) -> Optional[str]:
        """Get diff for a specific file"""
        try:
            result = subprocess.run(
                ["git", "diff", filename],
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )
            
            if result.returncode == 0 and result.stdout:
                return result.stdout
            return None
            
        except Exception:
            return None
    
    def get_commit_history(self, limit: int = 10) -> List[Dict]:
        """Get recent commit history"""
        try:
            result = subprocess.run(
                ["git", "log", f"--max-count={limit}", "--pretty=format:%H|%an|%ad|%s", "--date=short"],
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )
            
            if result.returncode != 0:
                return []
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) == 4:
                        commits.append({
                            "hash": parts[0][:8],
                            "author": parts[1],
                            "date": parts[2],
                            "message": parts[3]
                        })
            
            return commits
            
        except Exception:
            return []
    
    def get_file_content(self, filename: str, show_untracked: bool = False) -> Optional[str]:
        """Get current content of a file"""
        try:
            if show_untracked or os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    return f.read()
            return None
        except Exception:
            return None

# Initialize changes viewer
changes_viewer = SimpleChangesViewer()

@app.get("/", response_class=HTMLResponse)
async def view_changes(request: Request):
    """Main changes viewer page"""
    git_status = changes_viewer.get_git_status()
    commit_history = changes_viewer.get_commit_history()
    
    return templates.TemplateResponse(
        "changes.html",
        {
            "request": request,
            "git_status": git_status,
            "commit_history": commit_history,
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    )

@app.get("/diff/{filename:path}")
async def get_file_diff(filename: str):
    """Get diff for a specific file"""
    diff = changes_viewer.get_file_diff(filename)
    if diff is None:
        raise HTTPException(status_code=404, detail="No changes found for file")
    
    return {"filename": filename, "diff": diff}

@app.get("/content/{filename:path}")
async def get_file_content(filename: str):
    """Get current content of a file"""
    content = changes_viewer.get_file_content(filename, show_untracked=True)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {"filename": filename, "content": content}

@app.get("/api/status")
async def get_git_status():
    """Get current Git status as JSON"""
    return changes_viewer.get_git_status()

@app.get("/api/history")
async def get_commit_history(limit: int = 10):
    """Get commit history as JSON"""
    return changes_viewer.get_commit_history(limit)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    print("🚀 Starting Simple Changes Viewer...")
    print("📱 Open your browser and go to: http://localhost:8000")
    print("📝 View Git changes at: http://localhost:8000")
    print("🔌 Health check at: http://localhost:8000/health")
    print("📚 API docs at: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
