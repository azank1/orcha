"""Unit tests for OutputNormalizer."""

import pytest

from superagent.middleware.output_normalizer import OutputNormalizer


@pytest.mark.asyncio
async def test_plain_string_passthrough():
    result = await OutputNormalizer.normalize("Hello world", "MCP")
    assert result["content"] == "Hello world"
    assert result["artifact"] is None


@pytest.mark.asyncio
async def test_tmp_path_string_is_passthrough_not_auto_upload():
    """Bare /tmp paths are not uploaded here — save_artifact is the bookend."""
    sid = "session-abc"
    path_str = f"/tmp/{sid}/converted.pdf"
    result = await OutputNormalizer.normalize(
        path_str, "MCP", session_id=sid, user_id="user-1"
    )
    assert result["content"] == path_str
    assert result["artifact"] is None


@pytest.mark.asyncio
async def test_mcp_content_list_text():
    raw = {"content": [{"type": "text", "text": "Email received."}]}
    result = await OutputNormalizer.normalize(raw, "MCP")
    assert result["content"] == "Email received."
    assert result["artifact"] is None


@pytest.mark.asyncio
async def test_mcp_content_multiple_texts():
    raw = {
        "content": [
            {"type": "text", "text": "Part 1"},
            {"type": "text", "text": "Part 2"},
        ]
    }
    result = await OutputNormalizer.normalize(raw, "MCP")
    assert "Part 1" in result["content"]
    assert "Part 2" in result["content"]


@pytest.mark.asyncio
async def test_a2a_result_key():
    raw = {"result": "Task completed successfully"}
    result = await OutputNormalizer.normalize(raw, "A2A")
    assert result["content"] == "Task completed successfully"


@pytest.mark.asyncio
async def test_a2a_output_key():
    raw = {"output": "Done"}
    result = await OutputNormalizer.normalize(raw, "A2A")
    assert result["content"] == "Done"


@pytest.mark.asyncio
async def test_binary_bytes_become_artifact():
    data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    result = await OutputNormalizer.normalize(data, "MCP")
    assert result["artifact"] is not None
    assert result["artifact"].mime_type == "application/octet-stream"
    assert "[Artifact:" in result["content"] or "ARTIFACT PRODUCED" in result["content"]


@pytest.mark.asyncio
async def test_mcp_image_content_becomes_artifact():
    import base64

    png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
    raw = {
        "content": [
            {
                "type": "image",
                "mimeType": "image/png",
                "data": base64.b64encode(png_data).decode(),
            }
        ]
    }
    result = await OutputNormalizer.normalize(raw, "MCP")
    assert result["artifact"] is not None
    assert result["artifact"].mime_type == "image/png"
