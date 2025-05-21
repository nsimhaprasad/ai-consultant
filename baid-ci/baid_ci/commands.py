import json
import os
import re
import subprocess
import sys
import traceback
from typing import Dict, Tuple, Optional, List
from pydantic import BaseModel
import requests
from rich.console import Console
from rich.markdown import Markdown
import io

from .spinner import Spinner


def format_markdown_for_terminal(text: str) -> str:
    """Format markdown text for terminal display using rich"""
    if not text:
        return ""
    
    # Create a console that captures output
    console = Console(color_system="truecolor", width=80, file=io.StringIO())
    
    # Render the markdown
    md = Markdown(text)
    console.print(md, end="")
    
    # Get the rendered output
    return console.file.getvalue()

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
            data = line[6:].strip()
            if data.startswith("{\"error\":"):
                try:
                    error = json.loads(data)    
                    result["error"] = error["error"]
                except json.JSONDecodeError as e:
                    result["error"] = data
                return result
            
            # Check for end of stream
            if data == "[DONE]":
                break
            
            # Handle multi-line JSON objects by tracking brace count
            json_builder = [data]
            brace_count = data.count('{') - data.count('}')
            
            # Continue reading lines until we have a complete JSON object
            while brace_count > 0 and i < len(lines):
                next_line = lines[i].strip()
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
    if "error" in analysis:
        print(f"Some error occurred while analyzing the error. Please try again.\n{analysis['error']}")
        return

    print("\n" + "=" * 80)
    print("🔍 BAID-CI ERROR ANALYSIS")
    print("=" * 80)

    if "error_analysis" in analysis:
        print("\n❌ ERROR: " + analysis["error_analysis"])

    print("\n" + "=" * 80)
    if "brief_explanation" in analysis:
        # Format and print the explanation with markdown formatting
        explanation = analysis["brief_explanation"].strip()
        print("\n💡 BRIEF EXPLANATION:")
        print(format_markdown_for_terminal(explanation))

    print("\n" + "=" * 80)
    if "probable_fix" in analysis:
        # Format and print the probable fix with markdown formatting
        probable_fix = analysis["probable_fix"].strip()
        print("\n💻 PROBABLE FIX:")
        print(format_markdown_for_terminal(probable_fix))

    print("\n" + "=" * 80)