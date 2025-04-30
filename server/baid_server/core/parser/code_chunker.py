"""
Code chunking service for processing codebase files.
"""

import os
from typing import Any, Dict, List, Optional

from baid_server.core.parser.tree_sitter_parser import tree_sitter_parser

# logger = get_logger(__name__)


class CodeChunker:
    """Code chunking service."""

    def __init__(self):
        """Initialize code chunker."""
        self.parser = tree_sitter_parser

    async def process_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """
        Process a file and extract code chunks.

        Args:
            file_path: Path to the file.
            content: File content.

        Returns:
            List of code chunk dictionaries.
        """
        # Detect language
        language = self.parser.detect_language(file_path)
        if not language:
            # logger.warning(f"Unsupported file type: {file_path}")
            return []

        # Extract chunks
        chunks = self.parser.extract_chunks(content, language, file_path)

        # Add relationships between chunks
        chunks = self._add_relationships(chunks)

        # logger.info(f"Extracted {len(chunks)} chunks from {file_path}")
        return chunks

    def _add_relationships(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Add parent-child relationships between chunks.

        Args:
            chunks: List of code chunk dictionaries.

        Returns:
            Updated list of code chunk dictionaries.
        """
        # Sort chunks by start position
        sorted_chunks = sorted(
            chunks, key=lambda x: (x["start_line"], x["start_column"])
        )

        # Build a map of chunk positions
        chunk_map = {}
        for i, chunk in enumerate(sorted_chunks):
            key = (
                chunk["start_line"],
                chunk["start_column"],
                chunk["end_line"],
                chunk["end_column"],
            )
            chunk_map[key] = i

        # Find parent chunks
        for i, chunk in enumerate(sorted_chunks):
            parent_idx = self._find_parent(chunk, sorted_chunks, i)
            if parent_idx is not None:
                chunk["parent_id"] = sorted_chunks[parent_idx]["id"]

        return sorted_chunks

    def _find_parent(
        self, chunk: Dict[str, Any], all_chunks: List[Dict[str, Any]], chunk_idx: int
    ) -> Optional[int]:
        """
        Find parent chunk for a given chunk.

        Args:
            chunk: Chunk dictionary.
            all_chunks: List of all chunks.
            chunk_idx: Index of the current chunk.

        Returns:
            Index of the parent chunk or None if no parent found.
        """
        # Get chunk position
        start_line = chunk["start_line"]
        start_col = chunk["start_column"]
        end_line = chunk["end_line"]
        end_col = chunk["end_column"]

        # Find possible parent chunks
        # A parent chunk must contain the current chunk
        candidates = []
        for i, other in enumerate(all_chunks):
            if i == chunk_idx:
                continue

            other_start_line = other["start_line"]
            other_start_col = other["start_column"]
            other_end_line = other["end_line"]
            other_end_col = other["end_column"]

            # Check if other chunk contains this chunk
            is_contained = (
                other_start_line < start_line
                or (other_start_line == start_line and other_start_col <= start_col)
            ) and (
                other_end_line > end_line
                or (other_end_line == end_line and other_end_col >= end_col)
            )

            if is_contained:
                candidates.append((i, other))

        # If no candidates, there's no parent
        if not candidates:
            return None

        # Find the closest parent (smallest containing chunk)
        closest_parent = None
        closest_size = float("inf")

        for i, candidate in candidates:
            size = (candidate["end_line"] - candidate["start_line"]) * 1000 + (
                candidate["end_column"] - candidate["start_column"]
            )

            if size < closest_size:
                closest_size = size
                closest_parent = i

        return closest_parent

    async def process_directory(
        self, dir_path: str, ignore_patterns: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process a directory and extract code chunks from all files.

        Args:
            dir_path: Path to the directory.
            ignore_patterns: Optional list of patterns to ignore.

        Returns:
            List of code chunk dictionaries.
        """
        if not ignore_patterns:
            ignore_patterns = [
                "__pycache__",
                "node_modules",
                ".git",
                ".idea",
                ".vscode",
                "*.pyc",
                "*.pyo",
                "*.pyd",
                "*.so",
                "*.dll",
            ]

        all_chunks = []

        # Walk directory
        for root, dirs, files in os.walk(dir_path):
            # Filter directories
            dirs[:] = [
                d
                for d in dirs
                if not any(
                    pattern in d
                    for pattern in ignore_patterns
                    if not pattern.startswith("*")
                )
            ]

            # Process files
            for file in files:
                # Check if file should be ignored
                if any(
                    pattern.replace("*", "") in file
                    for pattern in ignore_patterns
                    if pattern.startswith("*")
                ):
                    continue

                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, dir_path)

                try:
                    # Read file content
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Process file
                    chunks = await self.process_file(relative_path, content)
                    all_chunks.extend(chunks)
                except Exception as e:
                    print(f"Failed to process {file_path}: {str(e)}")
                    # logger.warning(f"Failed to process {file_path}: {str(e)}")

        # logger.info(f"Processed {len(all_chunks)} chunks from directory {dir_path}")
        return all_chunks


# Create instance for dependency injection
code_chunker = CodeChunker()
