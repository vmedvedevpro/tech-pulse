from anthropic.types import MessageParam, ToolResultBlockParam

from techpulse.agent.core.memory import SlidingWindowStrategy


def _user(text: str) -> MessageParam:
    return MessageParam(role="user", content=text)


def _assistant(text: str = "ok") -> MessageParam:
    return MessageParam(role="assistant", content=text)


def _tool_result(tool_use_id: str = "call_1") -> MessageParam:
    return MessageParam(
        role="user",
        content=[ToolResultBlockParam(type="tool_result", tool_use_id=tool_use_id, content="result")],
    )


class TestSlidingWindowStrategy:
    def test_trim_returns_empty_list_unchanged(self):
        strategy = SlidingWindowStrategy(max_turns=5)

        result = strategy.trim([])

        assert result == []

    def test_trim_returns_unchanged_when_below_max_turns(self):
        strategy = SlidingWindowStrategy(max_turns=3)
        messages = [_user("hi"), _assistant(), _user("how are you"), _assistant()]

        result = strategy.trim(messages)

        assert result == messages

    def test_trim_returns_unchanged_when_equal_to_max_turns(self):
        strategy = SlidingWindowStrategy(max_turns=2)
        messages = [_user("hi"), _assistant(), _user("how are you"), _assistant()]

        result = strategy.trim(messages)

        assert result == messages

    def test_trim_drops_oldest_turn_when_one_over_max(self):
        strategy = SlidingWindowStrategy(max_turns=1)
        messages = [_user("old"), _assistant(), _user("new"), _assistant()]

        result = strategy.trim(messages)

        assert result == [_user("new"), _assistant()]

    def test_trim_keeps_exactly_max_turns(self):
        strategy = SlidingWindowStrategy(max_turns=2)
        messages = [
            _user("turn1"), _assistant(),
            _user("turn2"), _assistant(),
            _user("turn3"), _assistant(),
        ]

        result = strategy.trim(messages)

        assert result == messages[2:]

    def test_trim_preserves_tool_cycle_within_kept_window(self):
        strategy = SlidingWindowStrategy(max_turns=1)
        kept = [_user("fetch it"), _assistant("calling"), _tool_result(), _assistant("done")]
        messages = [_user("old"), _assistant()] + kept

        result = strategy.trim(messages)

        assert result == kept

    def test_trim_drops_tool_cycle_from_evicted_turn(self):
        strategy = SlidingWindowStrategy(max_turns=1)
        evicted = [_user("old"), _assistant("calling"), _tool_result(), _assistant("done")]
        kept = [_user("new"), _assistant()]
        messages = evicted + kept

        result = strategy.trim(messages)

        assert result == kept

    def test_trim_does_not_count_tool_results_as_turns(self):
        # Three tool_result messages + one real user turn should be treated as 1 turn total
        strategy = SlidingWindowStrategy(max_turns=1)
        messages = [
            _user("go"),
            _assistant("calling"),
            _tool_result("a"),
            _assistant("calling again"),
            _tool_result("b"),
            _assistant("done"),
        ]

        result = strategy.trim(messages)

        assert result == messages
