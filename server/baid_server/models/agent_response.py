import json
import re
from baid_server.core.models import JetbrainsResponse


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

        inner_json_str = match.group(2).encode('utf-8').decode('unicode_escape')

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


def parse_ci_agent_response(response_chunk):
    """Extract text content from the agent response without attempting full JSON parsing.
    
    This function extracts the text content directly using string manipulation and regex,
    avoiding the complexity of parsing nested JSON with potentially invalid escape sequences.
    
    Args:
        response_chunk: The response chunk from the agent, can be bytes or string
        
    Returns:
        Dict with content_type and data keys
        
    Raises:
        ValueError: If text content cannot be extracted
    """
    if isinstance(response_chunk, bytes):
        chunk_str = response_chunk.decode('utf-8')
    else:
        chunk_str = str(response_chunk)
    
    # Extract text directly from the data format
    # First, isolate the data portion
    data_pattern = re.compile(r'data:\s*"(.+?)(?="\n\w+\s*\{)', re.DOTALL)
    data_match = data_pattern.search(chunk_str)
    
    if data_match:
        data_str = data_match.group(1)
        # Un-escape the string to get valid JSON content
        try:
            decoded_data = data_str.encode('utf-8').decode('unicode_escape')
            
            # Now extract the text field using a more precise pattern
            text_pattern = re.compile(r'"parts":\s*\[\{"text":\s*"(.+?)"\}\]', re.DOTALL)
            text_match = text_pattern.search(decoded_data)
            
            if text_match:
                text_content = text_match.group(1)
                # The text content itself might have escaped characters
                text_content = text_content.replace('\\n', '\n').replace('\\"', '"')
                
                return {
                    "content_type": "application/json",
                    "data": text_content
                }
        except Exception:
            # If the above approach fails, try a simpler direct extraction
            pass
    
    # Fallback approaches if the primary method fails
    # Try to find text directly with a simpler pattern
    simple_pattern = re.compile(r'"text":\s*"(.+?)(?=",\s*"role"|"\}\])', re.DOTALL)
    simple_match = simple_pattern.search(chunk_str)
    
    if simple_match:
        try:
            text_content = simple_match.group(1)
            text_content = text_content.encode('utf-8').decode('unicode_escape')
            return {
                "content_type": "application/json",
                "data": text_content
            }
        except Exception:
            pass
    
    # Last resort: try to extract anything between "text": and the next field
    last_pattern = re.compile(r'"text":\s*"(.+?)"', re.DOTALL)
    last_match = last_pattern.search(chunk_str)
    
    if last_match:
        try:
            text_content = last_match.group(1)
            text_content = text_content.encode('utf-8').decode('unicode_escape')
            return {
                "content_type": "application/json",
                "data": text_content
            }
        except Exception:
            pass
    
    raise ValueError("Could not extract text from chunk")


def parse_agent_stream(stream_response):
    for chunk in stream_response:
        try:
            agent_response = parse_agent_response(chunk)

            yield agent_response
        except ValueError as e:
            print(f"Warning: {e}")
            continue

def parse_ci_response(stream_response):
    for chunk in stream_response:
        try:
            ci_response = parse_ci_agent_response(chunk)

            yield ci_response
        except ValueError as e:
            print(f"Warning: {e}")
            continue
