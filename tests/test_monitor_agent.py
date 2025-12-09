"""Tests for MonitorAgent MVP."""

import tempfile
from pathlib import Path
from agents.monitor.monitor_agent import MonitorAgent, MonitorIssue


def test_monitor_agent_detects_errors():
    """Test that MonitorAgent detects error patterns in log files."""
    agent = MonitorAgent()
    
    # Create a temporary log file with errors
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        log_file = Path(f.name)
        f.write("2024-12-08 10:00:00 INFO: Application started\n")
        f.write("2024-12-08 10:01:00 ERROR: Database connection failed\n")
        f.write("2024-12-08 10:02:00 Exception: Connection timeout\n")
        f.write("2024-12-08 10:03:00 Traceback (most recent call last):\n")
        f.write("2024-12-08 10:04:00 WARNING: High memory usage\n")
        f.write("2024-12-08 10:05:00 HTTP 500 Internal Server Error\n")
    
    try:
        result = agent.analyze_logs([log_file], max_lines=100)
        
        # Should detect multiple issues
        assert len(result.issues) > 0
        
        # Should have at least one error
        error_issues = [i for i in result.issues if i.severity == "error"]
        assert len(error_issues) > 0
        
        # Check that specific patterns were detected
        error_codes = [i.code for i in result.issues]
        assert "ERROR_LINE" in error_codes or "EXCEPTION" in error_codes
        
        # Summary should mention errors
        assert "error" in result.summary.lower()
        
    finally:
        log_file.unlink()


def test_monitor_agent_handles_missing_file():
    """Test that MonitorAgent handles missing log files gracefully."""
    agent = MonitorAgent()
    
    missing_file = Path("/nonexistent/path/to/log.log")
    result = agent.analyze_logs([missing_file], max_lines=100)
    
    # Should report file not found as warning
    assert len(result.issues) > 0
    assert any(i.code == "FILE_NOT_FOUND" for i in result.issues)


def test_monitor_agent_detects_warnings():
    """Test that MonitorAgent detects warning patterns."""
    agent = MonitorAgent()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        log_file = Path(f.name)
        f.write("2024-12-08 10:00:00 WARNING: Deprecated API usage\n")
        f.write("2024-12-08 10:01:00 WARN: Low disk space\n")
        f.write("2024-12-08 10:02:00 Timeout: Request took too long\n")
    
    try:
        result = agent.analyze_logs([log_file], max_lines=100)
        
        # Should detect warnings
        warning_issues = [i for i in result.issues if i.severity == "warning"]
        assert len(warning_issues) > 0
        
    finally:
        log_file.unlink()


def test_monitor_agent_empty_file():
    """Test that MonitorAgent handles empty log files."""
    agent = MonitorAgent()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        log_file = Path(f.name)
        # Write nothing (empty file)
    
    try:
        result = agent.analyze_logs([log_file], max_lines=100)
        
        # Should return empty issues list
        assert len(result.issues) == 0
        assert "0 issue" in result.summary.lower()
        
    finally:
        log_file.unlink()

