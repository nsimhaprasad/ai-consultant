from pprint import pprint

import pytest
from pathlib import Path
from baid_server.core.parser.code_chunker import CodeChunker


@pytest.mark.asyncio
async def test_process_file_python_function_chunk():
    code = """
def foo(x):
    return x + 1

def bar(y):
    return y * 2
"""
    file_path = "example.py"
    chunker = CodeChunker()
    chunks = await chunker.process_file(file_path, code)

    print("chunks", chunks)
    # Should extract two function chunks
    assert isinstance(chunks, list)
    assert len(chunks) == 2
    names = {chunk["name"] for chunk in chunks}
    assert "foo" in names and "bar" in names
    for chunk in chunks:
        assert chunk["language"] == "python"
        assert chunk["type"] == "function_definition"
        assert chunk["start_line"] < chunk["end_line"]


@pytest.mark.asyncio
async def test_process_file_unsupported_language():
    code = "<html><body></body></html>"
    file_path = "index.html"
    chunker = CodeChunker()
    chunks = await chunker.process_file(file_path, code)
    assert chunks == []


@pytest.mark.asyncio
async def test_process_file_empty_content():
    code = ""
    file_path = "empty.py"
    chunker = CodeChunker()
    chunks = await chunker.process_file(file_path, code)
    print("chunks", chunks)
    assert chunks == []


@pytest.mark.asyncio
async def test_relationships_are_added():
    code = """
class Foo:
    def method_a(self):
        pass
    def method_b(self):
        pass
"""
    file_path = "foo.py"
    chunker = CodeChunker()
    chunks = await chunker.process_file(file_path, code)
    print("chunks", chunks)
    # Should extract a class and its methods, with relationships
    class_chunk = next((c for c in chunks if c["type"] == "class_definition"), None)
    method_chunks = [c for c in chunks if c["type"] == "function_definition"]
    assert class_chunk is not None
    for method in method_chunks:
        assert "parent" in method
        assert method["parent"] == class_chunk["id"]
