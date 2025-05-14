import json
import os
import re
import subprocess
import sys
import traceback
from typing import Dict, Tuple, Optional, List
from pydantic import BaseModel
import requests

from .spinner import Spinner

# ANSI color codes for terminal formatting
COLORS = {
    'RESET': '\033[0m',
    'BOLD': '\033[1m',
    'ITALIC': '\033[3m',
    'UNDERLINE': '\033[4m',
    'BLACK': '\033[30m',
    'RED': '\033[31m',
    'GREEN': '\033[32m',
    'YELLOW': '\033[33m',
    'BLUE': '\033[34m',
    'MAGENTA': '\033[35m',
    'CYAN': '\033[36m',
    'WHITE': '\033[37m',
    'BRIGHT_BLACK': '\033[90m',  # Gray
    'BRIGHT_RED': '\033[91m',
    'BRIGHT_GREEN': '\033[92m',
    'BRIGHT_YELLOW': '\033[93m',
    'BRIGHT_BLUE': '\033[94m',
    'BRIGHT_MAGENTA': '\033[95m',
    'BRIGHT_CYAN': '\033[96m',
    'BRIGHT_WHITE': '\033[97m',
}


def format_markdown_for_terminal(text: str) -> str:
    """Format markdown text for terminal display with ANSI colors
    
    Handles common markdown elements like headers, lists, code blocks,
    bold and italic text, and inline code.
    """
    if not text:
        return ""
    
    # Process code blocks with or without language specification
    def replace_code_block(match):
        if match.group(1):
            language = match.group(1).strip()
            code = match.group(2).strip()
        else:
            language = ""
            code = match.group(2).strip()
        
        formatted_code = []
        for line in code.split('\n'):
            formatted_code.append(f"  {COLORS['BRIGHT_BLACK']}{line}{COLORS['RESET']}")
            
        return f"\n{COLORS['BOLD']}Code{' (' + language + ')' if language else ''}:{COLORS['RESET']}\n{'\n'.join(formatted_code)}\n"
    
    # First handle code blocks (must be done before inline elements)
    text = re.sub(r'```([\w]*)[\s\n]*(.*?)```', replace_code_block, text, flags=re.DOTALL)
    
    # Handle inline code
    text = re.sub(r'`([^`]+)`', f"{COLORS['BRIGHT_BLACK']}\1{COLORS['RESET']}", text)
    
    # Handle headers
    text = re.sub(r'^(#{1,6})\s+(.+)$', 
                 lambda m: f"\n{COLORS['BOLD']}{COLORS['BRIGHT_WHITE']}{' ' * (len(m.group(1))-1)}{'#' if len(m.group(1)) <= 3 else '-'} {m.group(2)}{COLORS['RESET']}", 
                 text, 
                 flags=re.MULTILINE)
    
    # Handle bold text
    text = re.sub(r'\*\*(.+?)\*\*', f"{COLORS['BOLD']}\1{COLORS['RESET']}", text)
    
    # Handle italic text
    text = re.sub(r'\*([^\*]+)\*', f"{COLORS['ITALIC']}\1{COLORS['RESET']}", text)
    
    # Handle unordered lists
    text = re.sub(r'^(\s*)[-*]\s+(.+)$', 
                 lambda m: f"{m.group(1)}• {COLORS['BRIGHT_WHITE']}\2{COLORS['RESET']}", 
                 text, 
                 flags=re.MULTILINE)
    
    # Handle ordered lists
    text = re.sub(r'^(\s*)(\d+)\.\s+(.+)$', 
                 lambda m: f"{m.group(1)}{COLORS['BRIGHT_YELLOW']}{m.group(2)}.{COLORS['RESET']} {COLORS['BRIGHT_WHITE']}\3{COLORS['RESET']}", 
                 text, 
                 flags=re.MULTILINE)
    
    # Add extra spacing for readability
    text = re.sub(r'\n{3,}', '\n\n', text)  # Normalize multiple blank lines
    
    return text

# Constants
CI_ANALYZE_URL = os.environ.get("BAID_CI_ANALYZE_URL", "https://core.baid.dev/api/ci/analyze")


def execute_command(command: str) -> Tuple[int, str, str]:
    """Execute a command and capture its output"""
    print(f"Running command: {command}")

    # Create a subprocess
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Capture and forward stdout and stderr in real-time
    stdout_lines = []
    stderr_lines = []

    # Process stdout
    for line in iter(process.stdout.readline, ""):
        stdout_lines.append(line)
        sys.stdout.write(line)

    # Process stderr
    for line in iter(process.stderr.readline, ""):
        stderr_lines.append(line)
        sys.stderr.write(line)

    # Wait for process to complete
    exit_code = process.wait()

    # Combine captured output
    stdout = "".join(stdout_lines)
    stderr = "".join(stderr_lines)

    return exit_code, stdout, stderr


class Block(BaseModel):
    type: str
    content: str


def process_streaming_response(response) -> Dict:
    """Process the streaming response from the API (SSE)"""
    result = {}
    full_text = ""

    try:
        # Process the streaming response line by line like in the Kotlin implementation
        lines = response.content.decode('utf-8').splitlines()
        line_count = 0
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            line_count += 1
            
            i += 1  # Move to next line
            
            # Skip lines that don't start with "data: "
            if not line.startswith("data: "):
                continue
                
            # Extract data portion
            data = line[6:].strip()  # Skip "data: " prefix
            
            # Check for end of stream
            if data == "[DONE]":
                break
            
            # Handle multi-line JSON objects by tracking brace count
            json_builder = [data]
            brace_count = data.count('{') - data.count('}')
            
            # Continue reading lines until we have a complete JSON object
            while brace_count > 0 and i < len(lines):
                next_line = lines[i].strip()
                print(f"[STREAM] continuation: {next_line}")
                json_builder.append(next_line)
                brace_count += next_line.count('{') - next_line.count('}')
                i += 1
                line_count += 1
            
            # Join all lines to form complete JSON string
            json_str = ''.join(json_builder)
            
            try:
                # Parse the complete JSON object
                data = json.loads(json_str)
                
                # Create Block object and process based on type
                data_block = Block(**data)
                block_type = data_block.type
                
                # Map the content to the appropriate result field based on type
                if block_type == "error_analysis":
                    result["error_analysis"] = data["content"]
                elif block_type == "brief_explanation":
                    result["brief_explanation"] = data["content"]
                elif block_type == "probable_fix":
                    result["probable_fix"] = data["content"]
                    
            except json.JSONDecodeError as e:
                print(f"JSON parsing failed: {e}")
                print(f"Error at position {e.pos}, line {e.lineno}, column {e.colno}")
                print(f"JSON string: {json_str}")
                
                # Try to fix common JSON issues
                try:
                    # Replace problematic escaped quotes
                    fixed_str = json_str.replace('\\"', '"')
                    # Fix unescaped backslashes that should be escaped
                    fixed_str = re.sub(r'([^\\])"', r'\1\\"', fixed_str)
                    fixed_str = re.sub(r'^"', '\\"', fixed_str)
                    # Fix trailing commas
                    fixed_str = re.sub(r',\s*}', '}', fixed_str)
                    fixed_str = re.sub(r',\s*\]', ']', fixed_str)
                    
                    print(f"Attempting with fixed JSON: {fixed_str[:100]}...")
                    data = json.loads(fixed_str)
                    
                    # Process the fixed JSON
                    data_block = Block(**data)
                    block_type = data_block.type
                    
                    if block_type == "error_analysis":
                        result["error_analysis"] = data["content"]
                    elif block_type == "brief_explanation":
                        result["brief_explanation"] = data["content"]
                    elif block_type == "probable_fix":
                        result["probable_fix"] = data["content"]
                        
                except Exception as inner_e:
                    print(f"Failed to fix JSON: {inner_e}")
                    continue
                    
            except Exception as e:
                print(f"Error processing JSON object: {e}")
                traceback.print_exc()
                continue
    
    except Exception as e:
        print(f"Error in stream processing: {e}")
        traceback.print_exc()
        
    return result


def run_ci_analysis(command, stdout, stderr, config):
    """Run CI error analysis by POSTing to /api/ci/analyze and returning the parsed result."""
    endpoint = CI_ANALYZE_URL
    request_data = {
        "command": command,
        "stdout": stdout,
        "stderr": stderr,
        "environment": getattr(config, 'environment', None),
        "metadata": getattr(config, 'metadata', None)
    }
    headers = {"Content-Type": "application/json"}
    # Attach authentication if available
    token = getattr(config, 'token', None)
    auth_type = getattr(config, 'auth_type', None)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        print(f"Sending CI error analysis request to {endpoint}")
        response = requests.post(endpoint, headers=headers, data=json.dumps(request_data), stream=True)
        if response.status_code != 200:
            error_text = response.text[:200] + "..." if len(response.text) > 200 else response.text
            return {"solution": f"API error: HTTP {response.status_code}", "explanation": f"Failed to get a response from BAID.dev:\n{error_text}"}
        analysis_result = process_streaming_response(response)
        return analysis_result
    finally:
        pass


def print_analysis(analysis: Dict) -> None:
    """Print a concise version of the analysis results to stdout"""
    print("\n" + "=" * 80)
    print("🔍 BAID-CI ERROR ANALYSIS")
    print("=" * 80)

    if "error_analysis" in analysis:
        print("\n❌ ERROR: " + analysis["error_analysis"])

    print("=" * 80)
    if "brief_explanation" in analysis:
        # Format and print the explanation with markdown formatting
        explanation = analysis["brief_explanation"].strip()
        print("\n💡 BRIEF EXPLANATION:")
        print(format_markdown_for_terminal(explanation))

    print("=" * 80)
    if "probable_fix" in analysis:
        # Format and print the probable fix with markdown formatting
        probable_fix = analysis["probable_fix"].strip()
        print("\n💻 PROBABLE FIX:")
        print(format_markdown_for_terminal(probable_fix))

    print("\n" + "=" * 80)