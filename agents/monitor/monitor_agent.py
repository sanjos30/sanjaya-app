"""Monitor agent for reading logs and detecting issues."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class MonitorIssue:
    """Represents a detected issue in logs."""
    severity: str  # "info", "warning", "error"
    code: str  # e.g., "ERROR_LINE", "TIMEOUT_PATTERN"
    message: str
    line: str
    line_number: Optional[int]
    file_path: str


@dataclass
class MonitorResult:
    """Result of log analysis."""
    issues: List[MonitorIssue]
    summary: str


class MonitorAgent:
    """Agent that observes logs/metrics and identifies issues."""
    
    def __init__(self, llm_client=None):
        """
        Initialize monitor agent.
        
        Args:
            llm_client: LLM client (optional, not used in MVP)
        """
        self.llm_client = llm_client
    
    def analyze_logs(self, log_files: List[Path], max_lines: int = 2000) -> MonitorResult:
        """
        Analyze log files and detect issues.
        
        MVP behaviour:
        - Read up to max_lines from each file (tail or entire file)
        - Detect lines containing common error patterns
        - Return MonitorResult with summary and list of issues
        
        Args:
            log_files: List of log file paths
            max_lines: Maximum lines to read per file
            
        Returns:
            MonitorResult: Analysis result with issues and summary
        """
        issues: List[MonitorIssue] = []
        
        for log_file in log_files:
            if not log_file.exists():
                issues.append(MonitorIssue(
                    severity="warning",
                    code="FILE_NOT_FOUND",
                    message=f"Log file not found: {log_file}",
                    line="",
                    line_number=None,
                    file_path=str(log_file)
                ))
                continue
            
            try:
                file_issues = self._analyze_single_file(log_file, max_lines)
                issues.extend(file_issues)
            except Exception as e:
                issues.append(MonitorIssue(
                    severity="error",
                    code="FILE_READ_ERROR",
                    message=f"Error reading log file: {str(e)}",
                    line="",
                    line_number=None,
                    file_path=str(log_file)
                ))
        
        # Generate summary
        error_count = len([i for i in issues if i.severity == "error"])
        warning_count = len([i for i in issues if i.severity == "warning"])
        info_count = len([i for i in issues if i.severity == "info"])
        
        summary = f"Found {len(issues)} issue(s): {error_count} error(s), {warning_count} warning(s), {info_count} info"
        
        return MonitorResult(issues=issues, summary=summary)
    
    def _analyze_single_file(self, log_file: Path, max_lines: int) -> List[MonitorIssue]:
        """Analyze a single log file for issues."""
        issues: List[MonitorIssue] = []
        
        # Read file (tail if too large)
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
                # If file is too large, take last max_lines
                if len(lines) > max_lines:
                    lines = lines[-max_lines:]
                
                # Analyze each line
                for line_num, line in enumerate(lines, start=1):
                    line_issues = self._detect_line_issues(line, line_num, log_file)
                    issues.extend(line_issues)
        except Exception as e:
            issues.append(MonitorIssue(
                severity="error",
                code="FILE_READ_ERROR",
                message=f"Error reading file: {str(e)}",
                line="",
                line_number=None,
                file_path=str(log_file)
            ))
        
        return issues
    
    def _detect_line_issues(self, line: str, line_number: int, file_path: Path) -> List[MonitorIssue]:
        """Detect issues in a single log line."""
        issues: List[MonitorIssue] = []
        line_stripped = line.strip()
        
        if not line_stripped:
            return issues
        
        # Error patterns
        error_patterns = [
            (r'\bERROR\b', "ERROR_LINE", "error"),
            (r'\bException\b', "EXCEPTION", "error"),
            (r'\bTraceback\b', "TRACEBACK", "error"),
            (r'\bFATAL\b', "FATAL", "error"),
            (r'\bCRITICAL\b', "CRITICAL", "error"),
            (r'HTTP\s+5\d{2}', "HTTP_5XX", "error"),
            (r'\bFailed\b', "FAILED", "error"),
            (r'\bTimeout\b', "TIMEOUT", "warning"),
            (r'\bWARN\b', "WARN", "warning"),
            (r'\bWARNING\b', "WARNING", "warning"),
        ]
        
        for pattern, code, severity in error_patterns:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                issues.append(MonitorIssue(
                    severity=severity,
                    code=code,
                    message=f"Detected {code} pattern in log",
                    line=line_stripped[:200],  # Truncate long lines
                    line_number=line_number,
                    file_path=str(file_path)
                ))
                # Only report first match per line
                break
        
        return issues
    
    def read_logs(self, project_config: dict, since: str = None):
        """
        Read logs for a project (legacy method, kept for compatibility).
        
        Args:
            project_config: Project configuration
            since: Timestamp to read logs since
            
        Returns:
            list: Log entries
        """
        # Stub for now - can be enhanced later
        return []
    
    def detect_issues(self, logs: list):
        """
        Detect recurring issues in logs (legacy method).
        
        Args:
            logs: List of log entries
            
        Returns:
            list: Detected issues with frequency and severity
        """
        # Stub for now - can be enhanced later
        return []
    
    def identify_patterns(self, logs: list):
        """
        Identify patterns indicating problems (legacy method).
        
        Args:
            logs: List of log entries
            
        Returns:
            list: Identified patterns
        """
        # Stub for now - can be enhanced later
        return []
    
    def trigger_bugfix_workflow(self, issue: dict):
        """
        Trigger bugfix workflow for a detected issue (legacy method).
        
        Note: This is NOT implemented in MVP - MonitorAgent is on-demand only.
        
        Args:
            issue: Issue information
            
        Returns:
            dict: Workflow trigger result
        """
        # Stub - not implemented in MVP
        return {"status": "not_implemented", "message": "Auto-trigger not available in MVP"}

