import json
import logging
from typing import Optional, Dict, Any, List, AsyncGenerator

from pydantic import ValidationError

from baid_server.core.models import CiAnalyzerResponse

logger = logging.getLogger(__name__)
class CiResponseParser:
    @staticmethod
    async def process_incoming_chunk(event) -> Optional[str]:
        try:
            # Extract blocks from the cleaned JSON
            blocks = CiResponseParser.extract_blocks(CiAnalyzerResponse(**event))
            if blocks:
                for block in blocks:
                    # Format each block
                    formatted_block = CiResponseParser.format_block_for_sse(block, include_sse_format=True)
                    if formatted_block:
                        # Stream each block individually
                        print("Formatted block:", formatted_block)
                        yield formatted_block
        except Exception as e:
            logger.debug(f"Error processing chunk: {str(e)}")


    @staticmethod
    def extract_blocks(response: CiAnalyzerResponse) -> List[Dict[str, Any]]:
        json_buffer = str(json.dumps(response.dict()))
        try:
            return [block.dict() for block in response.response.content.blocks]
        except (json.JSONDecodeError, ValidationError, Exception) as e:
            # If complete parsing fails, try to extract blocks using regex
            logger.debug(f"JSON parsing error: {e}")
            import re
            blocks = []

            # Look for blocks array in the JSON
            blocks_match = re.search(r'"blocks"\s*:\s*\[(.*?)\]', json_buffer, re.DOTALL)
            if blocks_match:
                blocks_content = blocks_match.group(1)
                # Find individual JSON objects (blocks)
                block_pattern = re.compile(r'\{[^{}]*(\{[^{}]*\}[^{}]*)*\}')
                for match in block_pattern.finditer(blocks_content):
                    try:
                        block_json = match.group(0)
                        block_obj = json.loads(block_json)
                        # Validate block structure
                        if CiResponseParser.validate_block(block_obj):
                            blocks.append(block_obj)
                    except json.JSONDecodeError:
                        continue
            return blocks

    
    @staticmethod
    def validate_block(block_data: Dict[str, Any]) -> bool:
        if not isinstance(block_data, dict) or 'type' not in block_data:
            return False

        block_type = block_data.get('type')
        required_fields = {
            'error_analysis': ['content'],
            'brief_explanation': ['content'],
            'probable_fix': ['content']
        }

        if block_type not in required_fields:
            return False

        # Check if all required fields are present
        for field in required_fields[block_type]:
            if field not in block_data:
                return False

        return True

    @staticmethod
    def format_block_for_sse(block_obj: Dict[str, Any], include_sse_format: bool = True) -> Optional[str]:
        try:
            block_json = json.dumps(block_obj)

            # Either return just the JSON object or format it as an SSE message
            if include_sse_format:
                return f"data: {block_json}\n\n"
            else:
                return block_obj  # Return the block object directly for combining
        except Exception as e:
            logger.debug(f"Error formatting block for SSE: {str(e)}")
            return None
    