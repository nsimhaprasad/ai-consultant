"""
Enhanced code chunking service with language-specific optimizations.
"""
import os
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from baid_server.core.parser.tree_sitter_parser import tree_sitter_parser
from baid_server.utils.logging import get_logger

logger = get_logger(__name__)


class CodeChunker:
    """Code chunking service with language-specific optimizations."""

    def __init__(self):
        """Initialize the CodeChunker with a parser."""
        self.parser = tree_sitter_parser

    async def process_file(
            self,
            file_path: str,
            content: str,
            skip_relationships: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Process a source file and extract code chunks.

        Args:
            file_path: Path to the source file.
            content: Source code content.
            skip_relationships: Whether to skip adding relationships.

        Returns:
            List of code chunk dictionaries.
        """
        start_time = time.time()

        # Return empty list for empty content
        if not content or not content.strip():
            return []

        # Detect language
        language = self.parser.detect_language(file_path)
        if not language:
            logger.warning(f"Unsupported file type: {file_path}")
            return []

        # Extract chunks
        chunks = self.parser.extract_chunks(content, language, file_path)

        # Add relationships between chunks (unless skipped)
        if not skip_relationships:
            chunks = self._add_relationships(chunks)

        # Add metadata based on language
        chunks = self._add_language_metadata(chunks, language)

        processing_time = time.time() - start_time
        logger.info(f"Extracted {len(chunks)} chunks from {file_path} in {processing_time:.2f}s")
        return chunks

    def _add_language_metadata(
            self,
            chunks: List[Dict[str, Any]],
            language: str
    ) -> List[Dict[str, Any]]:
        """
        Add language-specific metadata to chunks.

        Args:
            chunks: List of code chunks.
            language: Programming language.

        Returns:
            Updated list of code chunks.
        """
        if language == "python":
            return self._add_python_metadata(chunks)
        elif language == "javascript":
            return self._add_javascript_metadata(chunks)
        elif language == "java":
            return self._add_java_metadata(chunks)
        elif language == "ruby":
            return self._add_ruby_metadata(chunks)
        else:
            return chunks

    def _chunk_by_indentation(
            self,
            lines: List[str],
            language: str,
            file_path: str
    ) -> List[Dict[str, Any]]:
        """
        Chunk Python code by indentation level.

        Args:
            lines: Code lines.
            language: Programming language.
            file_path: Path to the source file.

        Returns:
            List of code chunk dictionaries.
        """
        # Return empty list for empty content
        if not lines or all(not line.strip() for line in lines):
            return []
            
        chunks = []
        chunk_start = 0
        current_indent = 0
        in_chunk = False

        for i, line in enumerate(lines):
            # Skip empty lines
            if not line.strip():
                continue

            # Calculate indentation
            indent = len(line) - len(line.lstrip())

            # Detect chunk start (function or class definition)
            if (not in_chunk and
                    (line.strip().startswith("def ") or line.strip().startswith("class "))):
                chunk_start = i
                current_indent = indent
                in_chunk = True

            # Detect chunk end (dedent to same or lower level)
            elif (in_chunk and line.strip() and
                  indent <= current_indent and i > chunk_start + 1):
                # Extract chunk
                chunk_lines = lines[chunk_start:i]
                chunk_text = "\n".join(chunk_lines)

                # Determine chunk type
                chunk_type = "function_definition" if chunk_lines[0].strip().startswith("def ") else "class_definition"

                # Extract name
                first_line = chunk_lines[0].strip()
                name = first_line.split()[1].split("(")[0].strip(":")
                
                # Create chunk
                chunks.append({
                    "id": f"{file_path}:{chunk_start}:{i}",
                    "type": chunk_type,
                    "language": language,
                    "file_path": file_path,
                    "start_line": chunk_start,
                    "end_line": i - 1,
                    "start_column": current_indent,
                    "end_column": len(lines[i-1]),
                    "start_byte": sum(len(l) + 1 for l in lines[:chunk_start]),
                    "end_byte": sum(len(l) + 1 for l in lines[:i]) - 1,
                    "code_text": chunk_text,
                    "name": name,
                    "parent_id": None,
                })

                # Reset chunk tracking
                in_chunk = False

                # Check if this line starts a new chunk
                if (line.strip().startswith("def ") or line.strip().startswith("class ")):
                    chunk_start = i
                    current_indent = indent
                    in_chunk = True

        # Handle the last chunk if any
        if in_chunk:
            chunk_lines = lines[chunk_start:]
            chunk_text = "\n".join(chunk_lines)

            # Determine chunk type
            chunk_type = "function_definition" if chunk_lines[0].strip().startswith("def ") else "class_definition"
            
            # Extract name
            first_line = chunk_lines[0].strip()
            name = first_line.split()[1].split("(")[0].strip(":")

            # Create chunk
            chunks.append({
                "id": f"{file_path}:{chunk_start}:{len(lines)}",
                "type": chunk_type,
                "language": language,
                "file_path": file_path,
                "start_line": chunk_start,
                "end_line": len(lines) - 1,
                "start_column": current_indent,
                "end_column": len(lines[-1]),
                "start_byte": sum(len(l) + 1 for l in lines[:chunk_start]),
                "end_byte": sum(len(l) + 1 for l in lines),
                "code_text": chunk_text,
                "name": name,
                "parent_id": None,
            })

        return chunks

    def _chunk_by_window(
            self,
            lines: List[str],
            language: str,
            file_path: str
    ) -> List[Dict[str, Any]]:
        """
        Chunk code using a sliding window approach.

        Args:
            lines: Code lines.
            language: Programming language.
            file_path: Path to the source file.

        Returns:
            List of code chunk dictionaries.
        """
        # Return empty list for empty content
        if not lines or all(not line.strip() for line in lines):
            return []
            
        chunks = []
        
        # Define chunk size and overlap
        chunk_size = 50  # lines
        overlap = 10     # lines of overlap between chunks

        # Create chunks with overlap
        for i in range(0, len(lines), chunk_size - overlap):
            end = min(i + chunk_size, len(lines))

            # Skip small chunks at the end
            if end - i < 10 and i > 0:
                continue

            chunk_lines = lines[i:end]
            chunk_text = "\n".join(chunk_lines)

            # Calculate byte positions
            start_byte = sum(len(line) + 1 for line in lines[:i]) if i > 0 else 0
            end_byte = sum(len(line) + 1 for line in lines[:end]) - 1 if end > 0 else 0

            # Create chunk
            chunks.append({
                "id": f"{file_path}:{i}:{end}",
                "type": "block",
                "language": language,
                "file_path": file_path,
                "start_line": i,
                "end_line": end - 1,
                "start_column": 0,
                "end_column": len(chunk_lines[-1]) if chunk_lines else 0,
                "start_byte": start_byte,
                "end_byte": end_byte,
                "code_text": chunk_text,
                "name": f"Block {i//chunk_size + 1}",
                "parent_id": None,
            })

        return chunks

    def _add_python_metadata(
            self,
            chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Add Python-specific metadata to chunks.

        Args:
            chunks: List of code chunk dictionaries.

        Returns:
            Updated list of code chunk dictionaries.
        """
        for chunk in chunks:
            # Map type names to match test expectations
            if chunk["type"] == "FUNCTION":
                chunk["type"] = "function_definition"
            elif chunk["type"] == "CLASS":
                chunk["type"] = "class_definition"
            
            # Determine if it's a method or a function based on context
            if chunk["type"] == "function_definition" and chunk.get("context"):
                chunk["type"] = "method_definition"

            # Check for decorators in function/method definitions
            if chunk["type"] in ["function_definition", "method_definition"]:
                code_text = chunk["code_text"]
                decorator_lines = []
                for line in code_text.split("\n"):
                    if line.strip().startswith("@"):
                        decorator_name = line.strip()[1:].split("(")[0]
                        decorator_lines.append(decorator_name)

                if decorator_lines:
                    chunk["decorators"] = decorator_lines

                    # If this is a route handler, add that metadata
                    if any(d in ["route", "app.route", "get", "post", "put", "delete"] for d in decorator_lines):
                        chunk["is_route_handler"] = True

                    # Check for async functions
                    if "async " in code_text.split("def ")[0]:
                        chunk["is_async"] = True

            # Extract imports for import statements
            if chunk["type"] == "IMPORT":
                code_text = chunk["code_text"]
                import_modules = []

                if "import " in code_text:
                    if "from " in code_text:
                        # Case: from module import items
                        parts = code_text.split("from ")[1].split("import ")
                        if len(parts) > 1:
                            module = parts[0].strip()
                            items = [item.strip() for item in parts[1].split(",")]
                            import_modules = [f"{module}.{item}" for item in items]
                    else:
                        # Case: import module[, module2]
                        modules = code_text.replace("import ", "").split(",")
                        import_modules = [module.strip() for module in modules]

                if import_modules:
                    chunk["imported_modules"] = import_modules

        return chunks

    def _add_javascript_metadata(
            self,
            chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Add JavaScript-specific metadata to chunks.

        Args:
            chunks: List of code chunk dictionaries.

        Returns:
            Updated list of code chunk dictionaries.
        """
        for chunk in chunks:
            # Check for async functions/methods
            if chunk["type"] in ["function_definition", "method_definition"]:
                code_text = chunk["code_text"]
                if code_text.strip().startswith("async "):
                    chunk["is_async"] = True

            # Check for React components
            if chunk["type"] in ["function_definition", "class_definition"]:
                code_text = chunk["code_text"]

                # Function component: returns JSX
                if "return (" in code_text and ("<" in code_text and "/>" in code_text or ">" in code_text and "</" in code_text):
                    chunk["is_react_component"] = True
                    chunk["component_type"] = "function"

                # Class component: extends React.Component
                elif "extends " in code_text and ("Component" in code_text or "React.Component" in code_text):
                    chunk["is_react_component"] = True
                    chunk["component_type"] = "class"

            # Extract imports for import statements
            if chunk["type"] == "IMPORT":
                code_text = chunk["code_text"]
                import_modules = []

                if code_text.startswith("import "):
                    if " from " in code_text:
                        # Extract module name
                        module = code_text.split(" from ")[1].strip().strip(";").strip("'").strip('"')
                        import_modules.append(module)

                if import_modules:
                    chunk["imported_modules"] = import_modules

            # Check for exports
            if chunk["type"] == "EXPORT":
                chunk["is_exported"] = True

                if "default" in chunk["code_text"].split("export ")[1].split(" ")[0]:
                    chunk["is_default_export"] = True

        return chunks

    def _add_java_metadata(
            self,
            chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Add Java-specific metadata to chunks.

        Args:
            chunks: List of code chunk dictionaries.

        Returns:
            Updated list of code chunk dictionaries.
        """
        for chunk in chunks:
            # Check for annotations
            if chunk["type"] in ["class_definition", "function_definition", "method_definition", "field"]:
                code_text = chunk["code_text"]
                annotation_lines = []

                for line in code_text.split("\n"):
                    line = line.strip()
                    if line.startswith("@"):
                        annotation_name = line[1:].split("(")[0].strip()
                        annotation_lines.append(annotation_name)

                if annotation_lines:
                    chunk["annotations"] = annotation_lines

                    # Check for Spring/Jakarta EE annotations
                    spring_annotations = ["RestController", "Controller", "Service", "Repository", "Component", "Autowired"]
                    jakarta_annotations = ["Path", "GET", "POST", "PUT", "DELETE", "Produces", "Consumes"]

                    if any(anno in spring_annotations for anno in annotation_lines):
                        chunk["framework"] = "Spring"
                    elif any(anno in jakarta_annotations for anno in annotation_lines):
                        chunk["framework"] = "Jakarta EE"

            # Check for method signatures
            if chunk["type"] == "method_definition" or chunk["type"] == "function_definition":
                code_lines = chunk["code_text"].split("\n")
                signature_line = code_lines[0].strip()

                # Check for access modifiers
                if "public " in signature_line:
                    chunk["access_modifier"] = "public"
                elif "protected " in signature_line:
                    chunk["access_modifier"] = "protected"
                elif "private " in signature_line:
                    chunk["access_modifier"] = "private"

                # Check if static
                if "static " in signature_line:
                    chunk["is_static"] = True

                # Check if abstract
                if "abstract " in signature_line:
                    chunk["is_abstract"] = True

                # Check if final
                if "final " in signature_line:
                    chunk["is_final"] = True

            # Check for class modifiers
            if chunk["type"] == "class_definition":
                code_lines = chunk["code_text"].split("\n")
                class_line = code_lines[0].strip()

                # Check if abstract class
                if "abstract class" in class_line:
                    chunk["is_abstract"] = True

                # Check if final class
                if "final class" in class_line:
                    chunk["is_final"] = True

                # Check for extends
                if "extends" in class_line:
                    parent_class = class_line.split("extends")[1].split("{")[0].split("implements")[0].strip()
                    chunk["extends"] = parent_class

                # Check for implements
                if "implements" in class_line:
                    interfaces = class_line.split("implements")[1].split("{")[0].strip()
                    chunk["implements"] = [i.strip() for i in interfaces.split(",")]

        return chunks

    def _add_ruby_metadata(
            self,
            chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Add Ruby-specific metadata to chunks.

        Args:
            chunks: List of code chunk dictionaries.

        Returns:
            Updated list of code chunk dictionaries.
        """
        for chunk in chunks:
            # Extract require statements
            if "require" in chunk["code_text"] and chunk["code_text"].strip().startswith("require "):
                required_libs = []
                for line in chunk["code_text"].split("\n"):
                    line = line.strip()
                    if line.startswith("require ") or line.startswith("require_relative "):
                        lib = line.split("require")[1].strip().strip("'").strip('"')
                        required_libs.append(lib)

                if required_libs:
                    chunk["type"] = "REQUIRE"
                    chunk["required_libs"] = required_libs

            # Check for Rails-specific patterns
            if chunk["type"] == "class_definition":
                code_text = chunk["code_text"]

                # Check for ActiveRecord models
                if "< ActiveRecord::Base" in code_text or "< ApplicationRecord" in code_text:
                    chunk["is_rails_model"] = True

                    # Extract associations
                    associations = []
                    for line in code_text.split("\n"):
                        line = line.strip()
                        if any(assoc in line for assoc in ["has_many", "belongs_to", "has_one", "has_and_belongs_to_many"]):
                            associations.append(line)

                    if associations:
                        chunk["associations"] = associations

                # Check for Rails controllers
                if "< ApplicationController" in code_text or "< ActionController::Base" in code_text:
                    chunk["is_rails_controller"] = True

                    # Extract actions
                    actions = []
                    in_method = False
                    current_action = None

                    for line in code_text.split("\n"):
                        line = line.strip()
                        if line.startswith("def ") and not in_method:
                            current_action = line.split("def ")[1].split("(")[0].strip()
                            in_method = True
                            actions.append(current_action)
                        elif line == "end" and in_method:
                            in_method = False
                            current_action = None

                    if actions:
                        chunk["controller_actions"] = actions

            # Check for method visibility
            if chunk["type"] == "method_definition" or chunk["type"] == "function_definition":
                # Look for visibility modifiers in context
                code_lines = chunk["code_text"].split("\n")

                # Check for method visibility in preceding code
                for i, line in enumerate(code_lines):
                    if line.strip() in ["private", "protected", "public"]:
                        visibility = line.strip()
                        # Check if this is for the current method
                        if i < len(code_lines) - 1:
                            chunk["visibility"] = visibility
                            break

        return chunks

    def _add_relationships(
            self,
            chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Add parent-child relationships between chunks.

        Args:
            chunks: List of code chunk dictionaries.

        Returns:
            Updated list of code chunk dictionaries.
        """
        # Sort chunks by start position
        sorted_chunks = sorted(chunks, key=lambda x: (x["start_line"], x["start_column"]))

        # Build a map of chunk positions
        chunk_map = {}
        for i, chunk in enumerate(sorted_chunks):
            key = (chunk["start_line"], chunk["start_column"],
                   chunk["end_line"], chunk["end_column"])
            chunk_map[key] = i

        # Find parent chunks
        for i, chunk in enumerate(sorted_chunks):
            parent_idx = self._find_parent(chunk, sorted_chunks, i)
            if parent_idx is not None:
                chunk["parent_id"] = sorted_chunks[parent_idx]["id"]
                chunk["parent"] = sorted_chunks[parent_idx]["id"]  # Add this for compatibility with tests
                
                # If this is a function inside a class, mark it as a method
                if chunk["type"] == "function_definition" and sorted_chunks[parent_idx]["type"] == "class_definition":
                    chunk["type"] = "method_definition"

        return sorted_chunks

    def _find_parent(
            self,
            chunk: Dict[str, Any],
            all_chunks: List[Dict[str, Any]],
            chunk_idx: int
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
                    (other_start_line < start_line or
                     (other_start_line == start_line and other_start_col <= start_col)) and
                    (other_end_line > end_line or
                     (other_end_line == end_line and other_end_col >= end_col))
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
            size = (candidate["end_line"] - candidate["start_line"]) * 1000 + \
                   (candidate["end_column"] - candidate["start_column"])

            if size < closest_size:
                closest_size = size
                closest_parent = i

        return closest_parent

    async def process_directory(
            self,
            dir_path: str,
            ignore_patterns: Optional[List[str]] = None,
            recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Process a directory and extract code chunks from all files.

        Args:
            dir_path: Path to the directory.
            ignore_patterns: Optional list of patterns to ignore.
            recursive: Whether to process subdirectories recursively.

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
                "venv",
                "env",
                "build",
                "dist",
                "*.pyc",
                "*.pyo",
                "*.pyd",
                "*.so",
                "*.dll",
                "*.class",
                "*.jar",
                "*.war",
                "*.min.js",
                "*.bundle.js",
            ]

        all_chunks = []

        # Walk directory
        for root, dirs, files in os.walk(dir_path):
            # Skip processing subdirectories if not recursive
            if not recursive and root != dir_path:
                continue

            # Filter directories based on ignore patterns
            if ignore_patterns:
                dirs[:] = [d for d in dirs if not any(
                    pattern in d for pattern in ignore_patterns if not pattern.startswith("*")
                )]

            # Process files
            for file in files:
                # Check if file should be ignored
                if ignore_patterns and any(
                        pattern.replace("*", "") in file for pattern in ignore_patterns if pattern.startswith("*")
                ):
                    continue

                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, dir_path)

                try:
                    # Read the file content
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    
                    # Process file
                    chunks = await self.process_file(relative_path, content)
                    all_chunks.extend(chunks)
                except Exception as e:
                    logger.error(f"Failed to process file {file_path}: {str(e)}")
                    continue

        # Log the summary
        logger.info(f"Processed {len(all_chunks)} chunks from directory {dir_path}")
        return all_chunks


# Create instance for dependency injection
code_chunker = CodeChunker()
