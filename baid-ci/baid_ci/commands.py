"""Command execution and analysis module for BAID-CI

This module handles executing commands, analyzing errors, and presenting results.
"""

import json
import os
import subprocess
import sys
from typing import Dict, Tuple, Optional
import requests

from .spinner import Spinner

# Constants
CI_ANALYZE_URL = os.environ.get("BAID_CI_ANALYZE_URL", "http://localhost:8080/api/ci/analyze")


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


def process_streaming_response(response) -> Dict:
    """Process the streaming response from the API (SSE)"""
    result = {}
    session_id = None
    line_count = 0
    debug_print = False
    # Process each SSE message
    for line in response.iter_lines():
        if not line:
            continue
        line = line.decode('utf-8')
        line_count += 1
        if debug_print:
            print(f"DEBUG: Raw SSE line #{line_count}: {line[:100]}")
        if line.startswith(':'):
            continue
        if line.startswith('data:'):
            data = line[5:].strip()
            if debug_print:
                print(f"DEBUG: SSE data #{line_count}: {data[:100]}")
            if data == '[DONE]':
                break
            try:
                json_data = json.loads(data)
                if debug_print:
                    print(f"DEBUG: Parsed JSON #{line_count}: {str(json_data)[:100]}")
                if "session_id" in json_data:
                    session_id = json_data["session_id"]
                    result["session_id"] = session_id
                    continue
                for field in ["solution", "explanation", "code_change"]:
                    if field in json_data and json_data[field]:
                        result[field] = json_data[field]
                if "blocks" in json_data:
                    result["blocks"] = json_data["blocks"]
                if "all_blocks" in json_data:
                    result["all_blocks"] = json_data["all_blocks"]
            except json.JSONDecodeError:
                if debug_print:
                    print(f"DEBUG: Could not parse line #{line_count} as JSON: {data}")
                result["explanation"] = data
    if session_id and "session_id" not in result:
        result["session_id"] = session_id
    if not result:
        result = {"solution": "No structured response received", "explanation": "No output from CI analysis agent."}
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

    if "error" in analysis:
        print("\n❌ ERROR: " + analysis["error"])
        return

    # Extract the key information from blocks
    if "all_blocks" in analysis and analysis["all_blocks"]:
        blocks = analysis["all_blocks"]

        # First, find the main error description (usually in first paragraph)
        error_description = ""
        for block in blocks:
            if block.get("type") == "paragraph":
                error_description = block.get("content", "").strip()
                # Don't include lengthy error descriptions
                if len(error_description) > 300:
                    error_description = error_description[:297] + "..."
                break

        if error_description:
            print(f"\n🛑 ERROR: {error_description}")

        # Then, find the solution (usually after a "Solution" heading)
        solution_text = ""
        solution_found = False
        for i, block in enumerate(blocks):
            if block.get("type") == "heading" and "solution" in block.get("content", "").lower():
                solution_found = True
                # Take the paragraph that follows the heading
                if i + 1 < len(blocks) and blocks[i + 1].get("type") == "paragraph":
                    solution_text = blocks[i + 1].get("content", "").strip()
                continue

            # If we're after a solution heading, collect code blocks
            if solution_found and block.get("type") == "code":
                # We'll handle code blocks separately
                break

        if solution_text:
            print(f"\n✅ FIX: {solution_text}")

        # Find the from/to code change
        old_code = None
        new_code = None

        # Look for code blocks
        code_blocks = [block for block in blocks if block.get("type") == "code"]

        # If we have code blocks, find the one with the command (current/old code)
        # and the one with the suggested fix (new code)
        if len(code_blocks) >= 2:
            # First code block is often the command that was run (old code)
            old_code = code_blocks[0].get("content", "").strip()
            # The next code block is usually the suggested fix (new code)
            new_code = code_blocks[1].get("content", "").strip()

        # If we couldn't identify old/new code but have code blocks, just use the first one
        elif len(code_blocks) == 1:
            new_code = code_blocks[0].get("content", "").strip()

        # Print code change if we have it
        if old_code or new_code:
            print("\n📝 CODE CHANGE:")

            if old_code:
                print("\nFrom this:")
                print(f"```\n{old_code}\n```")

            if new_code:
                print("\nTo this:")
                print(f"```\n{new_code}\n```")

    # Fallback to traditional rendering if no blocks or we couldn't extract structured info
    else:
        if "solution" in analysis:
            print("\n📋 SUGGESTED FIX:")
            print(analysis["solution"])

        if "explanation" in analysis:
            # Only print first 5 lines of explanation
            explanation_lines = analysis["explanation"].strip().split('\n')[:5]
            print("\n💡 BRIEF EXPLANATION:")
            print('\n'.join(explanation_lines))

        if "code_change" in analysis:
            print("\n💻 CODE CHANGE:")
            print(f"```\n{analysis['code_change']}\n```")

    print("\n" + "=" * 80)