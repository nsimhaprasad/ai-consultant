import json
import re


class FunctionCallResponse(Exception):
    def __init__(self):
        super().__init__("Function call response")


def parse_langchain_agent_response(response_chunk):
    if isinstance(response_chunk, bytes):
        chunk_str = response_chunk.decode('utf-8')
    else:
        chunk_str = str(response_chunk)

    try:
        # Try to parse as direct JSON first
        data = json.loads(chunk_str)

        # Check if "output" key exists
        if "output" not in data:
            raise FunctionCallResponse()

        output_value = data["output"]

        # Remove ```json and ``` markers if present
        if isinstance(output_value, str):
            # Strip ```json from beginning and ``` from end
            output_value = re.sub(r'^```json\s*\n?', '', output_value)
            output_value = re.sub(r'\n?```\s*$', '', output_value)

            # Try to parse the cleaned output as JSON
            try:
                return json.loads(output_value)
            except json.JSONDecodeError:
                # If it's not JSON, return as string
                return output_value

        return output_value

    except json.JSONDecodeError:
        # If direct parsing fails, try the embedded JSON approach
        try:
            match = re.search(r'({.*"text":\s*")```json\\n(.*?)\\n```"', chunk_str, re.DOTALL)
            if not match:
                raise FunctionCallResponse()

            inner_json_str = match.group(2).encode('utf-8').decode('unicode_escape')
            inner_data = json.loads(inner_json_str)

            # Check if "output" key exists in the inner data
            if "output" not in inner_data:
                raise FunctionCallResponse()

            output_value = inner_data["output"]

            # Remove ```json and ``` markers if present
            if isinstance(output_value, str):
                output_value = re.sub(r'^```json\s*\n?', '', output_value)
                output_value = re.sub(r'\n?```\s*$', '', output_value)

                try:
                    return json.loads(output_value)
                except json.JSONDecodeError:
                    return output_value

            return output_value

        except Exception:
            raise FunctionCallResponse()

    except Exception as e:
        if isinstance(e, FunctionCallResponse):
            raise e
        raise FunctionCallResponse()


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


def parse_langchain_agent_stream(stream_response):
    for chunk in stream_response:
        if isinstance(chunk, bytes):
            chunk_str = chunk.decode('utf-8')
        else:
            chunk_str = str(chunk)

        if chunk_str.strip() == 'content_type: "application/json"':
            print("Skipping metadata header chunk")
            continue

        try:
            agent_response = parse_langchain_agent_response(chunk)
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
            ci_response = parse_ci_agent_response(chunk)

            yield ci_response
        except ValueError as e:
            print(f"Could not parse CI response: {e}")
            continue
