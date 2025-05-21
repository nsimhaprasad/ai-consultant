import json
import re


class FunctionCallResponse(Exception):
    def __init__(self):
        super().__init__("Function call response")

def parse_agent_response(response_chunk, is_ci=False):
    if isinstance(response_chunk, bytes):
        chunk_str = response_chunk.decode('utf-8')
    else:
        chunk_str = str(response_chunk)

    try:
        function_call_match = re.search(r'"function_call":\s*({.*?})(?=,|\s*})', chunk_str, re.DOTALL)
        if function_call_match:
            raise FunctionCallResponse()

        function_response_match = re.search(r'"function_response":\s*({.*?})(?=,|\s*})', chunk_str, re.DOTALL)
        if function_response_match:
            raise FunctionCallResponse()

        match = re.search(r'({.*"text":\s*")```json\\n(.*?)\\n```"', chunk_str, re.DOTALL)
        if not match:
            raise ValueError("Could not extract JSON from chunk")

        inner_json_str = match.group(2).encode('utf-8').decode('unicode_escape')
        inner_data = json.loads(inner_json_str)
        return inner_data
    except Exception as e:
        if isinstance(e, FunctionCallResponse):
            print("Function call response")
            raise e
        raise ValueError(f"Could not parse embedded text JSON: {e}")


def parse_ci_agent_response(json_string):
    # Step 1: Parse the outer JSON
    outer_json = json.loads(json_string)

    # Step 2: Extract the text field
    text_content = outer_json[0]["text"]

    # Step 3: Extract the inner JSON string from the markdown code block
    pattern = r'```json\n([\s\S]*?)\n```'
    match = re.search(pattern, text_content)

    if match:
        # Get the inner JSON string
        inner_json_str = match.group(1)

        # Step 4: Parse the inner JSON string
        try:
            inner_json = json.loads(inner_json_str)
            return inner_json
        except json.JSONDecodeError as e:
            print(f"Error parsing inner JSON: {e}")
            raise ValueError(f"Error parsing inner JSON: {e}")
    else:
        print("Failed to extract inner JSON from markdown code block")
        raise ValueError("Failed to extract inner JSON from markdown code block")

def parse_agent_stream(stream_response):
    for chunk in stream_response:
        if isinstance(chunk, bytes):
            chunk_str = chunk.decode('utf-8')
        else:
            chunk_str = str(chunk)
            
        if chunk_str.strip() == 'content_type: "application/json"':
            print("Skipping metadata header chunk")
            continue
            
        try:
            agent_response = parse_agent_response(chunk)
            yield agent_response
        except FunctionCallResponse as e:
            print(f"Function call response detected, skipping: {e}")
            continue
        except ValueError as e:
            print(f"Could not parse agent response: {e}")
            continue
        
def parse_ci_response(stream_response):
    for chunk in stream_response:
        if isinstance(chunk, bytes):
            chunk_str = chunk.decode('utf-8')
        else:
            chunk_str = str(chunk)

        if chunk_str.strip() == 'content_type: "application/json"':
            print("Skipping metadata header chunk")
            continue
        try:
            ci_response = parse_agent_response(chunk)

            yield ci_response
        except ValueError as e:
            print(f"Could not parse CI response: {e}")
            continue