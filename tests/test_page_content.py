"""Tests for narration text highlighting."""

from __future__ import annotations

from unravel.tui.widgets.page_content import styled_text


class TestStyledText:
    def test_plain_text_passthrough(self):
        t = styled_text("just plain narration")
        assert t.plain == "just plain narration"

    def test_inline_code_is_cyan(self):
        t = styled_text("Calls `to_dict` on the model")
        assert t.plain == "Calls to_dict on the model"
        styles = [str(span.style) for span in t.spans]
        assert any("cyan" in s and "bold" in s for s in styles)

    def test_bold_segment(self):
        t = styled_text("This is **important** stuff")
        assert t.plain == "This is important stuff"
        styles = [str(span.style) for span in t.spans]
        assert any(s == "bold" or s.endswith(" bold") for s in styles)

    def test_italic_segment(self):
        t = styled_text("Some *emphasis* here")
        assert t.plain == "Some emphasis here"
        styles = [str(span.style) for span in t.spans]
        assert any("italic" in s for s in styles)

    def test_base_style_applied_to_plain_runs(self):
        t = styled_text("plain `code` plain", base_style="bold")
        # base_style is attached as the segment style when present
        styles = [str(span.style) for span in t.spans]
        assert "bold" in styles  # for the surrounding plain text
        assert any("cyan" in s for s in styles)  # for the code

    def test_filename_with_dunder(self):
        t = styled_text("see `__init__.py` for setup")
        assert "__init__.py" in t.plain
        assert any("cyan" in str(s.style) for s in t.spans)

    def test_no_match_no_spans(self):
        t = styled_text("nothing fancy here")
        assert t.spans == []


class TestAutoDetect:
    def _styled_runs(self, content):
        """Return (text, style_str) tuples for code-styled spans."""
        t = styled_text(content)
        out = []
        for span in t.spans:
            style = str(span.style)
            if "cyan" in style:
                out.append(t.plain[span.start : span.end])
        return out

    def test_snake_case_function_name(self):
        runs = self._styled_runs("calls parse_diff to split hunks")
        assert "parse_diff" in runs

    def test_dunder(self):
        runs = self._styled_runs("the __init__ constructor")
        assert "__init__" in runs

    def test_function_call(self):
        runs = self._styled_runs("invokes analyze() on the provider")
        assert "analyze()" in runs

    def test_dotted_path(self):
        runs = self._styled_runs("reads walkthrough.threads from state")
        assert "walkthrough.threads" in runs

    def test_constant_name(self):
        runs = self._styled_runs("bumped MAX_JSON_RETRIES to 5")
        assert "MAX_JSON_RETRIES" in runs

    def test_filename(self):
        runs = self._styled_runs("update src/unravel/cli.py to add a flag")
        assert any(r.endswith("cli.py") for r in runs)

    def test_does_not_highlight_abbreviations(self):
        # i.e. and e.g. should be ignored (single-char dotted parts)
        runs = self._styled_runs("e.g. some text, i.e. another")
        assert runs == []

    def test_does_not_highlight_plain_words(self):
        runs = self._styled_runs("the function processes requests quickly")
        assert runs == []

    def test_explicit_backticks_still_work_alongside_autodetect(self):
        # Both `foo` (explicit) and bar_baz (auto) get highlighted
        runs = self._styled_runs("uses `foo` together with bar_baz")
        assert "foo" in runs
        assert "bar_baz" in runs
