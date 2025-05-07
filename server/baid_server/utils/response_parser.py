import json
import logging
from typing import Optional, Dict, Any, List, Tuple
from pydantic import ValidationError

from baid_server.core.models import JetbrainsResponse, Block

logger = logging.getLogger(__name__)

class ResponseParser:
    """
    A utility class for parsing and processing Jetbrains LLM responses.
    Follows Single Responsibility Principle by focusing solely on parsing and validation.
    """
    
    @staticmethod
    async def process_incoming_chunk(chunk: str, json_buffer: str) -> Optional[str]:
        try:
            # Try to parse the complete buffer as a JetbrainsResponse
            # Strip markdown code block formatting if present
            cleaned_json = json_buffer
            if json_buffer.startswith('```') and '```' in json_buffer[3:]:
                # Extract content between markdown code blocks
                start_idx = json_buffer.find('\n', 3) + 1
                end_idx = json_buffer.rfind('```')
                if start_idx > 0 and end_idx > start_idx:
                    cleaned_json = json_buffer[start_idx:end_idx].strip()
                else:
                    # Simpler fallback - just strip the markers
                    cleaned_json = json_buffer.strip('```json').strip('```')
            
            # Extract blocks from the cleaned JSON
            print("cleaned_json", cleaned_json)
            blocks = ResponseParser.extract_blocks(cleaned_json)
            print("blocks", blocks)
            if blocks:
                # Process all blocks and combine them into a single SSE message
                all_blocks_data = []
                for block in blocks:
                    # Format each block
                    formatted_block = ResponseParser.format_block_for_sse(block, include_sse_format=False)
                    if formatted_block:
                        all_blocks_data.append(formatted_block)
                
                # Combine all blocks into a single SSE message
                if all_blocks_data:
                    combined_data = json.dumps({"blocks": all_blocks_data})
                    return f"data: {combined_data}\n\n"
            
            return None
        except Exception as e:
            logger.debug(f"Error processing chunk: {str(e)}")
            return None
    
    @staticmethod
    def extract_blocks(json_buffer: str) -> List[Dict[str, Any]]:
        """
        Extract blocks from a complete or partial JSON response.
        
        Args:
            json_buffer: The accumulated JSON buffer
            
        Returns:
            List[Dict[str, Any]]: List of extracted blocks
        """
        try:
            # First try to parse as complete JSON
            response_data = json.loads(json_buffer)
            
            # Deserialize into a JetbrainsResponse object
            jetbrains_response = JetbrainsResponse(**response_data)
            
            # Extract blocks from the validated response
            return [block.dict() for block in jetbrains_response.response.content.blocks]
        except (json.JSONDecodeError, ValidationError, Exception) as e:
            # If complete parsing fails, try to extract blocks using regex
            print("JSON parsing error:", e)
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
                        if ResponseParser.validate_block(block_obj):
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
            'paragraph': ['content'],
            'heading': ['level', 'content'],
            'list': ['ordered', 'items'],
            'code': ['language', 'content'],
            'command': ['commandType', 'target', 'parameters'],
            'callout': ['style', 'content']
        }
        
        if block_type not in required_fields:
            return False
            
        # Check if all required fields are present
        for field in required_fields[block_type]:
            if field not in block_data:
                return False
                
        # Special handling for list items
        if block_type == 'list' and 'items' in block_data:
            items = block_data['items']
            if not isinstance(items, list):
                return False
                
            # Ensure all items have content
            for item in items:
                if not isinstance(item, dict) or 'content' not in item:
                    return False
        
        return True
    
    @staticmethod
    def format_block_for_sse(block_obj: Dict[str, Any], include_sse_format: bool = True) -> Optional[str]:
        """
        Format a block for Server-Sent Events (SSE).
        
        Args:
            block_obj: The block object to format
            
        Returns:
            Optional[str]: Formatted SSE data or None if invalid
        """
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
    
    @staticmethod
    def parse_jetbrains_response(json_data: str) -> Optional[JetbrainsResponse]:
        """
        Parse and validate a complete JetbrainsResponse.
        
        Args:
            json_data: The JSON string to parse
            
        Returns:
            Optional[JetbrainsResponse]: Parsed response or None if invalid
        """
        try:
            response_data = json.loads(json_data)
            return JetbrainsResponse(**response_data)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Error parsing JetbrainsResponse: {str(e)}")
            return None
