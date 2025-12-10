"""Repository client for local and remote repository operations."""

import os
import subprocess
from typing import Optional
try:
    from git import Repo, GitCommandError
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    # Create stub classes for when gitpython is not installed
    class Repo:
        pass
    class GitCommandError(Exception):
        pass
from pathlib import Path


class RepoClient:
    """Client for repository operations."""
    
    def __init__(self, repo_path: Optional[str] = None, github_token: Optional[str] = None):
        """
        Initialize repository client.
        
        Args:
            repo_path: Path to local repository (optional, can be set later)
            github_token: GitHub personal access token for authentication
            
        Raises:
            ImportError: If gitpython is not installed
        """
        if not GIT_AVAILABLE:
            raise ImportError(
                "GitPython is required for RepoClient. Install with: pip install gitpython"
            )
        
        self.repo_path = repo_path
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self._repo: Optional[Repo] = None
        
        if repo_path and os.path.exists(repo_path):
            self._repo = Repo(repo_path)
    
    def clone_repository(self, url: str, destination: str) -> str:
        """
        Clone a repository.
        
        Args:
            url: Repository URL (can include token for private repos)
            destination: Destination path
            
        Returns:
            str: Path to cloned repository
            
        Raises:
            GitCommandError: If clone fails
        """
        # Add token to URL if provided and URL doesn't already have auth
        clone_url = url
        if self.github_token and "github.com" in url and "@" not in url:
            # Insert token into URL: https://TOKEN@github.com/user/repo.git
            clone_url = url.replace("https://", f"https://{self.github_token}@")
        
        # Clone repository
        try:
            repo = Repo.clone_from(clone_url, destination)
            self.repo_path = destination
            self._repo = repo
            return destination
        except GitCommandError as e:
            raise RuntimeError(f"Failed to clone repository: {e}")
    
    def set_repo_path(self, repo_path: str):
        """
        Set the repository path and load repo.
        
        Args:
            repo_path: Path to repository
        """
        if not os.path.exists(repo_path):
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        self.repo_path = repo_path
        self._repo = Repo(repo_path)
    
    def _ensure_repo(self):
        """Ensure repo is loaded."""
        if not self._repo:
            if not self.repo_path:
                raise ValueError("No repository path set")
            if not os.path.exists(self.repo_path):
                raise ValueError(f"Repository path does not exist: {self.repo_path}")
            self._repo = Repo(self.repo_path)
    
    def create_branch(self, branch_name: str) -> bool:
        """
        Create a new branch.
        
        Args:
            branch_name: Name of the branch
            
        Returns:
            bool: True if branch was created, False if it already exists
        """
        self._ensure_repo()
        
        # Check if branch already exists
        if branch_name in [ref.name for ref in self._repo.heads]:
            return False
        
        # Create and checkout new branch
        self._repo.create_head(branch_name)
        self._repo.heads[branch_name].checkout()
        return True
    
    def checkout_branch(self, branch_name: str) -> bool:
        """
        Checkout an existing branch.
        
        Args:
            branch_name: Name of the branch
            
        Returns:
            bool: True if checkout successful, False if branch doesn't exist
        """
        self._ensure_repo()
        
        if branch_name not in [ref.name for ref in self._repo.heads]:
            return False
        
        self._repo.heads[branch_name].checkout()
        return True
    
    def commit_changes(self, message: str, files: Optional[list] = None) -> str:
        """
        Commit changes to repository.
        
        Args:
            message: Commit message
            files: List of file paths to commit (relative to repo root). If None, commits all changes.
            
        Returns:
            str: Commit hash
            
        Raises:
            GitCommandError: If commit fails
        """
        self._ensure_repo()
        
        # Stage files
        if files:
            for file_path in files:
                full_path = os.path.join(self.repo_path, file_path)
                if os.path.exists(full_path):
                    self._repo.index.add([file_path])
                else:
                    raise ValueError(f"File not found: {file_path}")
        else:
            # Stage all changes
            self._repo.index.add(["*"])
        
        # Commit
        try:
            commit = self._repo.index.commit(message)
            return commit.hexsha
        except GitCommandError as e:
            raise RuntimeError(f"Failed to commit changes: {e}")

    def create_pull_request_stub(self, branch_name: str, title: str, body: str = "") -> dict:
        """
        Stub method to represent PR creation. Does not call GitHub API.

        Returns a dict with PR metadata for downstream consumption.
        """
        self._ensure_repo()
        return {
            "branch": branch_name,
            "title": title,
            "body": body,
            "url": None,  # Not created in stub mode
            "status": "stub",
        }

    def push_branch(self, branch_name: str = "main", remote_name: str = "origin"):
        """
        Push a branch to the remote.
        """
        self._ensure_repo()
        try:
            remote = self._repo.remote(remote_name)
            remote.push(branch_name)
        except GitCommandError as e:
            raise RuntimeError(f"Failed to push branch {branch_name}: {e}")

    def create_pull_request(
        self,
        repo_full_name: str,
        head: str,
        base: str = "main",
        title: str = "",
        body: str = "",
        github_token: Optional[str] = None,
    ) -> dict:
        """
        Create a GitHub PR using REST API.
        Requires network access and a valid token.
        """
        token = github_token or self.github_token
        if not token:
            raise RuntimeError("GitHub token required for PR creation.")

        import requests  # type: ignore

        url = f"https://api.github.com/repos/{repo_full_name}/pulls"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
        }
        payload = {
            "title": title or head,
            "head": head,
            "base": base,
            "body": body or "",
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=20)
        if resp.status_code >= 300:
            raise RuntimeError(f"Failed to create PR: {resp.status_code} {resp.text}")
        return resp.json()
    
    def get_repo_info(self) -> dict:
        """
        Get repository information.
        
        Returns:
            dict: Repository information (remote URL, current branch, etc.)
        """
        self._ensure_repo()
        
        info = {
            "path": self.repo_path,
            "active_branch": self._repo.active_branch.name if self._repo.heads else None,
            "is_dirty": self._repo.is_dirty(),
            "remotes": {}
        }
        
        # Get remote URLs
        for remote in self._repo.remotes:
            info["remotes"][remote.name] = remote.url
        
        return info
    
    def write_file(self, file_path: str, content: str):
        """
        Write a file to the repository.
        
        Args:
            file_path: Path relative to repository root
            content: File content
        """
        self._ensure_repo()
        
        full_path = os.path.join(self.repo_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def read_file(self, file_path: str) -> str:
        """
        Read a file from the repository.
        
        Args:
            file_path: Path relative to repository root
            
        Returns:
            str: File content
        """
        self._ensure_repo()
        
        full_path = os.path.join(self.repo_path, file_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in the repository.
        
        Args:
            file_path: Path relative to repository root
            
        Returns:
            bool: True if file exists
        """
        self._ensure_repo()
        
        full_path = os.path.join(self.repo_path, file_path)
        return os.path.exists(full_path)
    
    def get_diff(self, base: str = "HEAD", target: Optional[str] = None) -> str:
        """
        Get unified diff between base and target (or working directory).
        
        Args:
            base: Base commit/branch (default: HEAD)
            target: Target commit/branch (default: working directory)
            
        Returns:
            str: Unified diff
        """
        self._ensure_repo()
        
        try:
            if target:
                diff = self._repo.git.diff(base, target)
            else:
                # Diff against working directory
                diff = self._repo.git.diff(base)
            return diff
        except GitCommandError as e:
            raise RuntimeError(f"Failed to get diff: {e}")

