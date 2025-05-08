"""Command execution and analysis module for BAID-CI

This module handles executing commands, analyzing errors, and presenting results.
"""

import json
import subprocess
import sys
from typing import Dict, Tuple, Optional
import requests

from .spinner import Spinner

# Constants
CONSULT_URL = "https://core.baid.dev/consult"


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
    """Process the streaming response from the API"""
    buffer = ""
    result = {}
    session_id = None
    line_count = 0
    block_count = 0

    # Process each SSE message
    for line in response.iter_lines():
        if not line:
            continue

        line = line.decode('utf-8')
        line_count += 1

        # Skip comments
        if line.startswith(':'):
            continue

        # Handle data lines
        if line.startswith('data:'):
            data = line[5:].strip()

            # Handle final message
            if data == '[DONE]':
                break

            try:
                json_data = json.loads(data)

                # Handle session ID
                if "session_id" in json_data:
                    session_id = json_data["session_id"]
                    result["session_id"] = session_id
                    continue

                # Handle error
                if "error" in json_data:
                    result["error"] = json_data["error"]
                    continue

                # Handle direct blocks array at the top level
                if "blocks" in json_data:
                    blocks = json_data.get("blocks", [])
                    block_count += len(blocks)

                    # Store blocks for rendering
                    if "all_blocks" not in result:
                        result["all_blocks"] = []

                    # Append blocks to our collected blocks
                    result["all_blocks"].extend(blocks)

                    # Process code blocks
                    for block in blocks:
                        if block["type"] == "code" and "code_change" not in result:
                            result["code_change"] = block["content"]

                # Handle content blocks inside content object
                elif "content" in json_data:
                    content = json_data.get("content", {})

                    if "solution" in content:
                        result["solution"] = content["solution"]

                    if "explanation" in content:
                        result["explanation"] = content["explanation"]

                    # Process blocks
                    if "blocks" in content:
                        blocks = content["blocks"]
                        block_count += len(blocks)

                        # Collect all blocks for rendering
                        if "all_blocks" not in result:
                            result["all_blocks"] = []
                        result["all_blocks"].extend(blocks)

                        # Process code blocks
                        for block in blocks:
                            if block["type"] == "code" and "code_change" not in result:
                                result["code_change"] = block["content"]
            except json.JSONDecodeError:
                # If not valid JSON, just append to buffer
                buffer += data

    # If we haven't extracted structured data, try to parse the buffer
    if not result and buffer:
        try:
            result = json.loads(buffer)
        except:
            result = {
                "solution": "Unstructured response received",
                "explanation": buffer
            }

    # Ensure session_id is included in the result
    if session_id and "session_id" not in result:
        result["session_id"] = session_id

    return result


def analyze_error(config, command: str, stdout: str, stderr: str) -> Dict:
    """Analyze the error using BAID.dev API with spinner to show progress"""
    print("\nAnalyzing error with BAID.dev AI...")

    # Prepare the prompt for the API
    prompt = f"""
I'm facing an error in my CI pipeline. Please help me fix it.

## Command
```
{command}
```

## Standard Output
```
{stdout}
```

## Error Output
```
{stderr}
```

Please analyze this error and provide a solution. Focus on the specific issue in the CI pipeline.
"""

    # Prepare the request data
    request_data = {
        "prompt": prompt,
        "context": {
            "is_open": False
        }
    }

    # Make the API request
    headers = {
        "Authorization": f"Bearer {config.token}",
        "Content-Type": "application/json"
    }

    if config.session_id:
        headers["session_id"] = config.session_id

    try:
        # Start spinner for visual feedback
        spinner = Spinner("Thinking ")
        spinner.start()

        try:
            response = requests.post(
                CONSULT_URL,
                headers=headers,
                json=request_data,
                stream=True  # Stream the response
            )

            if response.status_code != 200:
                spinner.stop()
                return {
                    "solution": f"API error: {response.text}",
                    "explanation": "Failed to get a response from BAID.dev"
                }

            # Process the streaming response
            analysis_result = process_streaming_response(response)

            # Save the session ID for future requests if it's in the response
            if "session_id" in analysis_result:
                config.session_id = analysis_result["session_id"]
                config.save()
        finally:
            # Make sure we stop the spinner in any case
            spinner.stop()

        return analysis_result
    except Exception as e:
        return {
            "solution": "Could not analyze error. Network or API error occurred.",
            "explanation": f"Exception: {str(e)}"
        }


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