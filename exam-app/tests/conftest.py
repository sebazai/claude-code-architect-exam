from __future__ import annotations

import pytest


@pytest.fixture
def mock_ctx():
    """MCP Context is unused by _sample_text in this repo; a MagicMock suffices."""
    from unittest.mock import MagicMock

    return MagicMock()
