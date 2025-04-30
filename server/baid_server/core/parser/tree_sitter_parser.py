"""
Tree-sitter integration for code parsing and chunking.
"""

import os
from typing import Any, Dict, List, Optional

from tree_sitter import Node, Parser, Tree

# logger = get_logger(__name__)

# Define supported languages and their file extensions
SUPPORTED_LANGUAGES = {
    "python": [".py"],
    "javascript": [".js", ".jsx", ".ts", ".tsx"],
    "java": [".java"],
    "c": [".c", ".h"],
    "cpp": [".cpp", ".hpp", ".cc", ".cxx"],
    "go": [".go"],
    "rust": [".rs"],
    "ruby": [".rb"],
    "php": [".php"],
    "csharp": [".cs"],
}


class TreeSitterParser:
    """Tree-sitter code parser integration."""

    _instance = None
    _initialized = False

    # Node types that represent code structural elements for each language
    LANGUAGE_NODE_TYPES = {
        "python": {
            "class": ["class_definition"],
            "function": ["function_definition"],
            "method": ["function_definition"],
            "variable": ["assignment"],
            "import": ["import_statement", "import_from_statement"],
        },
        "javascript": {
            "class": ["class_declaration", "class_expression"],
            "function": [
                "function_declaration",
                "function",
                "arrow_function",
                "method_definition",
            ],
            "method": ["method_definition"],
            "variable": ["variable_declaration", "lexical_declaration"],
            "import": ["import_statement"],
        },
        "java": {
            "class": ["class_declaration"],
            "interface": ["interface_declaration"],
            "method": ["method_declaration"],
            "field": ["field_declaration"],
            "import": ["import_declaration"],
        },
        # Add more languages as needed
    }

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super(TreeSitterParser, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Tree-sitter parser."""
        if not self._initialized:
            self._initialize_parser()
            self._initialized = True

    def _initialize_parser(self):
        """Initialize Tree-sitter parser and languages."""
        try:
            # Initialize parsers dictionary
            self.parsers = {}

            # Build and load languages
            self._build_languages()
            self._load_languages()

            # logger.info("Tree-sitter parser initialized successfully")
        except Exception as e:
            # logger.error(f"Failed to initialize Tree-sitter parser: {str(e)}")
            raise

    def _build_languages(self):
        """Build Tree-sitter languages if needed."""
        try:
            # Directory to store language libraries
            lib_dir = os.path.join(os.path.dirname(__file__), "tree-sitter-libs")
            os.makedirs(lib_dir, exist_ok=True)

            # Build path
            build_path = os.path.join(lib_dir, "languages.so")

            # Skip if already built
            if os.path.exists(build_path):
                # logger.info("Tree-sitter languages already built")
                return

            # Clone repositories and build languages
            # Note: In a real implementation, you would handle this more robustly
            # For example, checking out specific git commits of tree-sitter grammars
            # This is a simplified version
            # logger.info("Building Tree-sitter languages...")

            # For each supported language, you would need to clone its grammar repository
            # and build the language library
            # This is pseudo-code as actual implementation would involve git operations
            # which are beyond the scope of this example
            """
            Language.build_library(
                build_path,
                [
                    "./tree-sitter-python",
                    "./tree-sitter-javascript",
                    "./tree-sitter-java",
                    # Add more languages as needed
                ]
            )
            """

            # logger.info("Tree-sitter languages built successfully")
        except Exception as e:
            # logger.error(f"Failed to build Tree-sitter languages: {str(e)}")
            raise

    def _load_languages(self):
        """Load Tree-sitter languages."""
        try:
            # Language library path
            lib_path = os.path.join(
                os.path.dirname(__file__), "tree-sitter-libs", "languages.so"
            )

            # Load languages
            for lang in SUPPORTED_LANGUAGES.keys():
                self.parsers[lang] = Parser()

                # In a real implementation, you would load the language from the library
                # This is pseudo-code as the actual library doesn't exist in this example
                """
                language = Language(lib_path, lang)
                self.parsers[lang].set_language(language)
                """

            # logger.info(f"Loaded {len(self.parsers)} Tree-sitter languages")
        except Exception as e:
            # logger.error(f"Failed to load Tree-sitter languages: {str(e)}")
            raise

    def detect_language(self, file_path: str) -> Optional[str]:
        """
        Detect language from file extension.

        Args:
            file_path: Path to the file.

        Returns:
            Language name or None if unsupported.
        """
        ext = os.path.splitext(file_path)[1].lower()
        for lang, extensions in SUPPORTED_LANGUAGES.items():
            if ext in extensions:
                return lang
        return None

    def parse_code(self, code: str, language: str) -> Optional[Tree]:
        """
        Parse code using Tree-sitter.

        Args:
            code: Source code string.
            language: Programming language.

        Returns:
            Parsed syntax tree or None if parsing failed.
        """
        if language not in self.parsers:
            # logger.warning(f"Language {language} not supported")
            return None

        try:
            tree = self.parsers[language].parse(bytes(code, "utf8"))
            return tree
        except Exception as e:
            # logger.error(f"Failed to parse code: {str(e)}")
            return None

    def extract_chunks(
        self, code: str, language: str, file_path: str
    ) -> List[Dict[str, Any]]:
        """
        Extract code chunks from source code.

        Args:
            code: Source code string.
            language: Programming language.
            file_path: Path to the source file.

        Returns:
            List of code chunk dictionaries.
        """
        chunks = []
        tree = self.parse_code(code, language)

        if not tree:
            # logger.warning(
            #    # f"Failed to parse {file_path}, falling back to simple chunking"
            # )
            # Fall back to simple chunking (e.g., by indentation or line count)
            return self._simple_chunk(code, language, file_path)

        # Get root node
        root_node = tree.root_node

        # Get all top-level definitions
        top_level_nodes = self._get_top_level_nodes(root_node, language)

        # Process each top-level node
        for node in top_level_nodes:
            chunk = self._process_node(node, code, language, file_path)
            if chunk:
                chunks.append(chunk)

        # If no chunks were extracted, fall back to simple chunking
        if not chunks:
            # logger.warning(
            #    f"No chunks extracted from {file_path}, falling back to simple chunking"
            # )
            return self._simple_chunk(code, language, file_path)

        return chunks

    def _get_top_level_nodes(self, root_node: Node, language: str) -> List[Node]:
        """
        Get top-level nodes from the syntax tree.

        Args:
            root_node: Root node of the syntax tree.
            language: Programming language.

        Returns:
            List of top-level nodes.
        """
        nodes = []

        # Get node types for language
        language_types = self.LANGUAGE_NODE_TYPES.get(language, {})
        target_types = []
        for category in language_types.values():
            target_types.extend(category)

        # If language is not supported, return an empty list
        if not target_types:
            return []

        # Traverse children
        for child in root_node.children:
            if child.type in target_types:
                nodes.append(child)

        return nodes

    def _process_node(
        self, node: Node, code: str, language: str, file_path: str
    ) -> Optional[Dict[str, Any]]:
        """
        Process a node and extract a code chunk.

        Args:
            node: Syntax tree node.
            code: Source code string.
            language: Programming language.
            file_path: Path to the source file.

        Returns:
            Code chunk dictionary or None if not a valid chunk.
        """
        # Get node type
        node_type = node.type

        # Get node category
        category = None
        for cat, types in self.LANGUAGE_NODE_TYPES.get(language, {}).items():
            if node_type in types:
                category = cat
                break

        if not category:
            return None

        # Get code snippet
        start_byte = node.start_byte
        end_byte = node.end_byte
        snippet = code[start_byte:end_byte]

        # Get start and end positions
        start_point = node.start_point
        end_point = node.end_point

        # Get identifier (name)
        identifier = self._extract_identifier(node, language, code)

        # Create chunk
        chunk = {
            "id": f"{file_path}:{start_point[0]}:{start_point[1]}",
            "type": category.upper(),
            "language": language,
            "file_path": file_path,
            "start_line": start_point[0],
            "end_line": end_point[0],
            "start_column": start_point[1],
            "end_column": end_point[1],
            "start_byte": start_byte,
            "end_byte": end_byte,
            "code_text": snippet,
            "name": identifier or "",
            "parent_id": None,  # To be filled later
        }

        return chunk

    def _extract_identifier(
        self, node: Node, language: str, code: str
    ) -> Optional[str]:
        """
        Extract identifier (name) from a node.

        Args:
            node: Syntax tree node.
            language: Programming language.
            code: Source code string.

        Returns:
            Identifier string or None if not found.
        """
        # This is a simplified implementation
        # In a real parser, you would need to handle language-specific patterns
        if language == "python":
            # For Python, the identifier is usually the second child
            if node.child_count >= 2 and node.children[1].type == "identifier":
                return code[node.children[1].start_byte : node.children[1].end_byte]
        elif language == "javascript":
            # For JavaScript, look for identifier nodes
            for child in node.children:
                if child.type == "identifier":
                    return code[child.start_byte : child.end_byte]
        elif language == "java":
            # For Java, look for identifier nodes
            for child in node.children:
                if child.type == "identifier":
                    return code[child.start_byte : child.end_byte]

        return None

    def _simple_chunk(
        self, code: str, language: str, file_path: str
    ) -> List[Dict[str, Any]]:
        """
        Simple code chunking by indentation or line count.
        Used as a fallback when Tree-sitter parsing fails.

        Args:
            code: Source code string.
            language: Programming language.
            file_path: Path to the source file.

        Returns:
            List of code chunk dictionaries.
        """
        chunks = []
        lines = code.split("\n")

        # Chunk size in lines
        chunk_size = 50
        overlap = 10

        # Create chunks with overlap
        for i in range(0, len(lines), chunk_size - overlap):
            end = min(i + chunk_size, len(lines))
            chunk_lines = lines[i:end]
            chunk_text = "\n".join(chunk_lines)

            chunks.append(
                {
                    "id": f"{file_path}:{i}:{end}",
                    "type": "BLOCK",
                    "language": language,
                    "file_path": file_path,
                    "start_line": i,
                    "end_line": end - 1,
                    "start_column": 0,
                    "end_column": len(chunk_lines[-1]) if chunk_lines else 0,
                    "start_byte": (
                        sum(len(line) + 1 for line in lines[:i]) if i > 0 else 0
                    ),
                    "end_byte": (
                        sum(len(line) + 1 for line in lines[:end]) - 1 if end > 0 else 0
                    ),
                    "code_text": chunk_text,
                    "name": f"Block {i//chunk_size + 1}",
                    "parent_id": None,
                }
            )

        return chunks


# Create instance for dependency injection
tree_sitter_parser = TreeSitterParser()
