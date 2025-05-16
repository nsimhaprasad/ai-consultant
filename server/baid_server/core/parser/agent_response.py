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
        if is_ci:
            # Handle escape sequences manually
            inner_json_str = inner_json_str.replace('\\n', '\n')
            inner_json_str = inner_json_str.replace('\\\\', '\\').replace('\\n', '\n')
            # Fix any invalid escape sequences
            inner_json_str = re.sub(r'\\([^"\\/bfnrtu])', r'\1', inner_json_str)

        inner_data = json.loads(inner_json_str)
        return inner_data
    except Exception as e:
        if isinstance(e, FunctionCallResponse):
            print("Function call response")
            raise e
        raise ValueError(f"Could not parse embedded text JSON: {e}")


def parse_agent_stream(stream_response):
    for chunk in stream_response:
        if isinstance(chunk, bytes):
            chunk_str = chunk.decode('utf-8')
        else:
            chunk_str = str(chunk)
            
        if chunk_str.strip() == 'content_type: "application/json"':
            print("Skipping metadata header chunk")
            continue
            
        # if not chunk_str.strip():
        #     print("Skipping empty chunk")
        #     continue
            
        # if not re.search(r'"text":', chunk_str) and not re.search(r'"blocks":', chunk_str):
        #     print(f"Skipping non-content chunk: {chunk_str[:50]}...")
        #     continue
            
        # print(f"Processing chunk: {chunk_str[:50]}...")
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
        try:
            ci_response = parse_agent_response(chunk, is_ci=True)

            yield ci_response
        except ValueError as e:
            print(f"Could not parse CI response: {e}")
            continue
