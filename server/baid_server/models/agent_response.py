import json
import re
from baid_server.core.models import JetbrainsResponse


logger = logging.getLogger(__name__)
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


def parse_agent_stream(stream_response):
    for chunk in stream_response:
        try:
            agent_response = parse_agent_response(chunk)

            yield agent_response
        except ValueError as e:
            logger.warning(f"Could not parse agent response: {e}")
            continue

def parse_ci_response(stream_response):
    for chunk in stream_response:
        try:
            ci_response = parse_agent_response(chunk)

            yield ci_response
        except ValueError as e:
            logger.warning(f"Could not parse CI response: {e}")
            continue
