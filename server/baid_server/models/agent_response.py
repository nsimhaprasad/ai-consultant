import json
import re

def parse_agent_response(response_chunk):
    if isinstance(response_chunk, bytes):
        chunk_str = response_chunk.decode('utf-8')
    else:
        chunk_str = str(response_chunk)

    try:
        outer_data = json.loads(chunk_str)
    except json.JSONDecodeError:
        match = re.search(r'({.*"text":\s*")```json\\n(.*?)\\n```"', chunk_str, re.DOTALL)
        if not match:
            raise ValueError("Could not extract JSON from chunk")

        # inner_json_str = match.group(2).encode('utf-8').decode('unicode_escape')

        inner_json_str = match.group(2)
        # Handle escape sequences manually
        inner_json_str = inner_json_str.replace('\\\\', '\\').replace('\\n', '\n')
        # Fix any invalid escape sequences
        inner_json_str = re.sub(r'\\([^"\\/bfnrtu])', r'\1', inner_json_str)

        try:
            inner_data = json.loads(inner_json_str)
            return inner_data
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse embedded JSON: {e}")
    else:
        try:
            text = outer_data["content"]["parts"][0]["text"]
            cleaned = re.sub(r'^```json\n|```$', '', text.strip())
            parsed = json.loads(cleaned)
            return parsed
        except Exception as e:
            raise ValueError(f"Could not parse embedded text JSON: {e}")


def parse_agent_stream(stream_response):
    for chunk in stream_response:
        try:
            agent_response = parse_agent_response(chunk)

            yield agent_response
        except ValueError as e:
            print(f"Could not parse agent response: {e}")
            continue

def parse_ci_response(stream_response):
    for chunk in stream_response:
        try:
            ci_response = parse_agent_response(chunk)

            yield ci_response
        except ValueError as e:
            print(f"Could not parse CI response: {e}")
            continue
