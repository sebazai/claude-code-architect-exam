"""
Tests for get_next_question prefetch behaviour and session wiring.

Generation is mocked so tests run without MCP sampling or the claude CLI.
"""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_server import server as srv
from mcp_server.exam_content import MINI_EXAM_DURATION_SECONDS, MINI_QUESTIONS_PER_SCENARIO, MINI_TOTAL_QUESTIONS
from mcp_server.session import get_session, reset_session


def _fake_question(n: int) -> dict:
    return {
        "question": f"Question text {n}",
        "options": {"A": "a", "B": "b", "C": "c", "D": "d"},
        "correct": "A",
        "explanation": f"Explanation {n}",
    }


async def _start_exam_fixed_scenarios() -> None:
    await srv.start_exam()


async def _await_background_prefetch() -> None:
    """Ensure prefetch spawned by get_next_question finishes while mocks are still active."""
    session = get_session()
    if session is not None and session.prefetch_task is not None:
        await session.prefetch_task


@pytest.fixture(autouse=True)
def clean_session():
    reset_session()
    yield
    reset_session()


@pytest.mark.asyncio
async def test_get_next_question_requires_session(mock_ctx):
    reset_session()
    out = json.loads(await srv.get_next_question(mock_ctx))
    assert "error" in out
    err = out["error"].lower()
    assert "start_exam" in err and "mini" in err


@pytest.mark.asyncio
async def test_start_exam_mini_session_shape():
    with patch.object(srv.random, "sample", return_value=[1, 2, 3, 4]):
        out = json.loads(await srv.start_exam_mini())
    s = get_session()
    assert out["exam_mode"] == "mini"
    assert out["total_questions"] == MINI_TOTAL_QUESTIONS
    assert out["questions_per_scenario"] == MINI_QUESTIONS_PER_SCENARIO
    assert out["exam_duration_minutes"] == MINI_EXAM_DURATION_SECONDS // 60
    assert s.exam_mode == "mini"
    assert s.total_questions == MINI_TOTAL_QUESTIONS
    assert s.questions_per_scenario == MINI_QUESTIONS_PER_SCENARIO
    assert s.exam_duration_seconds == MINI_EXAM_DURATION_SECONDS


@pytest.mark.asyncio
async def test_first_question_no_prefetch_log(mock_ctx):
    with patch.object(srv.random, "sample", return_value=[1, 2, 3, 4]):
        await _start_exam_fixed_scenarios()
    gen = AsyncMock(side_effect=[(_fake_question(1), 5), (_fake_question(2), 5)])
    with patch.object(srv, "_generate_question_with_retry", gen):
        out = json.loads(await srv.get_next_question(mock_ctx))
        await _await_background_prefetch()
    assert out.get("question_number") == 1
    assert "Using prefetched" not in "\n".join(get_session().log_entries)
    gen.assert_awaited()


@pytest.mark.asyncio
async def test_second_question_uses_prefetch_log(mock_ctx):
    with patch.object(srv.random, "sample", return_value=[1, 2, 3, 4]):
        await _start_exam_fixed_scenarios()
    gen = AsyncMock(side_effect=[(_fake_question(1), 5), (_fake_question(2), 5)])
    with patch.object(srv, "_generate_question_with_retry", gen):
        await srv.get_next_question(mock_ctx)
        out = json.loads(await srv.get_next_question(mock_ctx))
    assert out.get("question_number") == 2
    log = "\n".join(get_session().log_entries)
    assert "Using prefetched Q2" in log
    assert gen.await_count == 2


@pytest.mark.asyncio
async def test_prefetch_task_started_after_first_question(mock_ctx):
    with patch.object(srv.random, "sample", return_value=[1, 2, 3, 4]):
        await _start_exam_fixed_scenarios()
    gen = AsyncMock(side_effect=[(_fake_question(1), 5), (_fake_question(2), 5)])
    # Keep the mock active while the background prefetch task runs (it outlives get_next_question).
    with patch.object(srv, "_generate_question_with_retry", gen):
        await srv.get_next_question(mock_ctx)
        session = get_session()
        assert session.prefetch_task is not None
        await session.prefetch_task
        assert session.prefetch_result is not None
        assert session.prefetch_result.get("for_question_number") == 2


@pytest.mark.asyncio
async def test_slow_prefetch_is_awaited_before_q2(mock_ctx):
    with patch.object(srv.random, "sample", return_value=[1, 2, 3, 4]):
        await _start_exam_fixed_scenarios()

    async def delayed_gen(ctx, *args, **kwargs):
        delayed_gen.calls += 1
        n = delayed_gen.calls
        if n >= 2:
            await asyncio.sleep(0.02)
        return _fake_question(n), 5

    delayed_gen.calls = 0

    with patch.object(srv, "_generate_question_with_retry", delayed_gen):
        await srv.get_next_question(mock_ctx)
        out = json.loads(await srv.get_next_question(mock_ctx))
    assert out.get("question_number") == 2
    assert "Waiting for prefetch of Q2" in "\n".join(get_session().log_entries)


@pytest.mark.asyncio
async def test_no_prefetch_after_final_question(mock_ctx):
    with patch.object(srv.random, "sample", return_value=[1, 2, 3, 4]):
        await _start_exam_fixed_scenarios()
    session = get_session()
    session.total_questions = 2
    gen = AsyncMock(side_effect=[(_fake_question(1), 5), (_fake_question(2), 5)])
    with patch.object(srv, "_generate_question_with_retry", gen):
        await srv.get_next_question(mock_ctx)
        await srv.get_next_question(mock_ctx)
        out = json.loads(await srv.get_next_question(mock_ctx))
    assert "error" in out
    session = get_session()
    assert session.prefetch_task is None


@pytest.mark.asyncio
async def test_compute_question_params_matches_direct_slot_logic(mock_ctx):
    """Regression: params helper stays aligned with scenario/domain slot selection."""
    with patch.object(srv.random, "sample", return_value=[1, 2, 3, 4]):
        await _start_exam_fixed_scenarios()
    session = get_session()
    from mcp_server.exam_content import QUESTIONS_PER_SCENARIO

    qn = 1
    params = srv._compute_question_params(session, qn)
    scenario_idx = (qn - 1) // QUESTIONS_PER_SCENARIO
    assert params[0] == session.selected_scenario_ids[scenario_idx]
    gen = AsyncMock(return_value=(_fake_question(1), 5))
    with patch.object(srv, "_generate_question_with_retry", gen):
        data = json.loads(await srv.get_next_question(mock_ctx))
        await _await_background_prefetch()
    assert data["scenario"] == params[1]["name"]
    assert data["domain"] == params[3]["name"]
