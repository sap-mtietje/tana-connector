"""Unit tests for description_utils"""

from app.utils.description_utils import strip_html, process_description


class TestStripHtml:
    """Tests for strip_html function"""

    def test_empty_string(self):
        """Test empty string returns empty"""
        assert strip_html("") == ""

    def test_none_returns_empty(self):
        """Test None-like falsy value returns empty"""
        assert strip_html(None) == ""

    def test_simple_html(self):
        """Test stripping simple HTML tags"""
        html = "<p>Hello World</p>"
        result = strip_html(html)
        assert "Hello World" in result

    def test_nested_html(self):
        """Test stripping nested HTML"""
        html = "<div><p>Nested <strong>content</strong></p></div>"
        result = strip_html(html)
        assert "Nested" in result
        assert "content" in result
        assert "<" not in result

    def test_removes_script_tags(self):
        """Test script tags are removed entirely"""
        html = "<p>Text</p><script>alert('xss')</script><p>More</p>"
        result = strip_html(html)
        assert "alert" not in result
        assert "Text" in result
        assert "More" in result

    def test_removes_style_tags(self):
        """Test style tags are removed entirely"""
        html = "<style>.class { color: red; }</style><p>Content</p>"
        result = strip_html(html)
        assert "color" not in result
        assert "Content" in result

    def test_removes_head_meta_link(self):
        """Test head, meta, link tags are removed"""
        html = "<head><meta charset='utf-8'><link rel='stylesheet'></head><body>Body</body>"
        result = strip_html(html)
        assert "charset" not in result
        assert "stylesheet" not in result
        assert "Body" in result

    def test_preserves_text_content(self):
        """Test text content is preserved"""
        html = "<div>First</div><div>Second</div>"
        result = strip_html(html)
        assert "First" in result
        assert "Second" in result


class TestProcessDescription:
    """Tests for process_description function"""

    def test_empty_description(self):
        """Test empty description returns empty"""
        assert process_description("") == ""

    def test_none_mode(self):
        """Test none mode returns empty"""
        assert process_description("Some content", mode="none") == ""

    def test_full_mode_preserves_html(self):
        """Test full mode preserves original content"""
        html = "<p>Hello</p>"
        result = process_description(html, mode="full")
        assert result == "<p>Hello</p>"

    def test_clean_mode_strips_html(self):
        """Test clean mode strips HTML"""
        html = "<p>Hello <strong>World</strong></p>"
        result = process_description(html, mode="clean")
        assert "<" not in result
        assert "Hello" in result
        assert "World" in result

    def test_clean_mode_normalizes_whitespace(self):
        """Test clean mode normalizes whitespace"""
        html = "<p>Line1</p>\r\n\r\n\r\n<p>Line2</p>"
        result = process_description(html, mode="clean")
        # Should not have excessive newlines
        assert "\r" not in result

    def test_truncation_with_max_length(self):
        """Test truncation at word boundary"""
        text = "This is a long description that should be truncated"
        result = process_description(text, mode="full", max_length=20)
        assert len(result) <= 23  # 20 + "..."
        assert result.endswith("...")

    def test_truncation_clean_mode(self):
        """Test truncation in clean mode"""
        html = "<p>This is a long description that should be truncated</p>"
        result = process_description(html, mode="clean", max_length=20)
        assert result.endswith("...")

    def test_no_truncation_when_short(self):
        """Test no truncation when content is short"""
        text = "Short"
        result = process_description(text, mode="full", max_length=100)
        assert result == "Short"
        assert "..." not in result

    def test_clean_mode_collapses_spaces(self):
        """Test clean mode collapses multiple spaces"""
        html = "<p>Word1    Word2</p>"
        result = process_description(html, mode="clean")
        assert "    " not in result

    def test_clean_mode_strips_empty_lines(self):
        """Test clean mode removes empty lines"""
        text = "Line1\n\n\n\nLine2"
        result = process_description(text, mode="clean")
        # Should have at most 2 consecutive newlines
        assert "\n\n\n" not in result
