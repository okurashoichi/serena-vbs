"""
Unit tests for ASP script extractor.

Tests the extraction of VBScript blocks from ASP files.
"""

import pytest

from solidlsp.language_servers.vbscript_lsp.asp_extractor import ASPScriptExtractor, ScriptBlock


@pytest.mark.vbscript
class TestASPDelimitedBlocks:
    """Test extraction of <% %> delimited blocks."""

    def test_extract_simple_block(self) -> None:
        """Test extraction of a simple <% %> block."""
        content = """<html>
<body>
<%
Dim x
x = 1
%>
</body>
</html>"""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        assert len(blocks) == 1
        block = blocks[0]
        assert "Dim x" in block.content
        assert "x = 1" in block.content
        assert block.start_line == 2  # Line where <% starts (0-indexed)
        assert block.is_inline is False

    def test_extract_multiple_blocks(self) -> None:
        """Test extraction of multiple <% %> blocks."""
        content = """<%
Dim a
%>
<html>
<%
Dim b
%>
</html>"""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        assert len(blocks) == 2
        assert "Dim a" in blocks[0].content
        assert "Dim b" in blocks[1].content

    def test_inline_expression_excluded(self) -> None:
        """Test that <%= %> inline expressions are excluded."""
        content = """<html>
<p>Value: <%= GetValue() %></p>
<%
Function GetValue()
    GetValue = 42
End Function
%>
</html>"""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        # Only the <% %> block should be extracted, not <%= %>
        assert len(blocks) == 1
        assert "Function GetValue" in blocks[0].content
        # The inline expression content should NOT be in any block
        for block in blocks:
            assert block.is_inline is False

    def test_block_position_tracking(self) -> None:
        """Test that block positions are correctly tracked."""
        content = """Line 0
Line 1
<%
Code here
%>
Line 5"""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        assert len(blocks) == 1
        block = blocks[0]
        assert block.start_line == 2  # <% is on line 2 (0-indexed)

    def test_empty_block(self) -> None:
        """Test extraction of empty block."""
        content = """<% %>"""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        assert len(blocks) == 1
        assert blocks[0].content.strip() == ""


@pytest.mark.vbscript
class TestASPScriptTags:
    """Test extraction of <script runat="server"> blocks."""

    def test_extract_script_tag(self) -> None:
        """Test extraction of <script runat="server"> block."""
        content = """<html>
<script language="vbscript" runat="server">
Function ServerFunc()
    ServerFunc = 1
End Function
</script>
</html>"""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        assert len(blocks) == 1
        block = blocks[0]
        assert "Function ServerFunc" in block.content
        assert block.is_inline is False

    def test_script_tag_case_insensitive(self) -> None:
        """Test that script tag detection is case-insensitive."""
        content = """<SCRIPT RUNAT="SERVER">
Sub TestSub()
End Sub
</SCRIPT>"""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        assert len(blocks) == 1
        assert "Sub TestSub" in blocks[0].content

    def test_script_tag_with_language_attr(self) -> None:
        """Test script tag with language attribute."""
        content = """<script language="VBScript" runat="server">
Dim value
</script>"""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        assert len(blocks) == 1
        assert "Dim value" in blocks[0].content

    def test_mixed_delimiters_and_script_tags(self) -> None:
        """Test file with both <% %> and <script> blocks."""
        content = """<%
Dim x
%>
<script runat="server">
Function GetX()
    GetX = x
End Function
</script>"""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        assert len(blocks) == 2
        contents = [b.content for b in blocks]
        assert any("Dim x" in c for c in contents)
        assert any("Function GetX" in c for c in contents)


@pytest.mark.vbscript
class TestASPBlockPositions:
    """Test accurate position calculation for ASP blocks."""

    def test_start_character_tracking(self) -> None:
        """Test that start character position is tracked."""
        content = """<html><% Dim x %></html>"""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        assert len(blocks) == 1
        block = blocks[0]
        assert block.start_line == 0
        assert block.start_character > 0  # Should be after <html>

    def test_multiline_block_end_position(self) -> None:
        """Test end position tracking for multiline blocks."""
        content = """<%
Line 1
Line 2
Line 3
%>"""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        assert len(blocks) == 1
        block = blocks[0]
        assert block.start_line == 0
        assert block.end_line == 4  # %> is on line 4


@pytest.mark.vbscript
class TestASPEdgeCases:
    """Test edge cases for ASP extraction."""

    def test_no_asp_blocks(self) -> None:
        """Test file with no ASP blocks."""
        content = """<html>
<body>
<p>Plain HTML</p>
</body>
</html>"""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        assert len(blocks) == 0

    def test_asp_comments(self) -> None:
        """Test ASP blocks with VBScript comments."""
        content = """<%
' This is a comment
Dim x  ' Inline comment
%>"""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        assert len(blocks) == 1
        assert "' This is a comment" in blocks[0].content

    def test_nested_html_in_asp(self) -> None:
        """Test ASP with Response.Write containing HTML."""
        content = """<%
Response.Write "<p>Hello</p>"
%>"""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        assert len(blocks) == 1
        assert 'Response.Write "<p>Hello</p>"' in blocks[0].content

    def test_empty_file(self) -> None:
        """Test empty file."""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract("")

        assert len(blocks) == 0

    def test_only_inline_expressions(self) -> None:
        """Test file with only inline expressions."""
        content = """<p><%= value1 %></p>
<p><%= value2 %></p>"""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        # Inline expressions should be excluded
        assert len(blocks) == 0


@pytest.mark.vbscript
class TestASPPositionOffset:
    """Test position offset calculation accuracy."""

    def test_offset_single_block_first_line(self) -> None:
        """Test offset when block starts on first line."""
        content = """<%
Function OnFirstLine()
End Function
%>"""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        assert len(blocks) == 1
        block = blocks[0]
        # Block starts at line 0
        assert block.start_line == 0
        # Content should include the function
        assert "Function OnFirstLine" in block.content

    def test_offset_after_html_header(self) -> None:
        """Test offset when block is after HTML header."""
        # Lines:
        # 0: <%@ Language="VBScript" %>
        # 1: <!DOCTYPE html>
        # 2: <html>
        # 3: <%
        # 4: Function InBody()
        # 5: End Function
        # 6: %>
        content = """<%@ Language="VBScript" %>
<!DOCTYPE html>
<html>
<%
Function InBody()
End Function
%>"""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        # Should extract 2 blocks: the directive and the code block
        code_blocks = [b for b in blocks if "Function" in b.content]
        assert len(code_blocks) == 1
        block = code_blocks[0]
        assert block.start_line == 3  # <% starts on line 3

    def test_offset_multiple_blocks_sequential(self) -> None:
        """Test offset calculation for sequential blocks."""
        content = """<%
' Block 1 - line 1
%>
<%
' Block 2 - line 4
%>
<%
' Block 3 - line 7
%>"""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        assert len(blocks) == 3
        assert blocks[0].start_line == 0
        assert blocks[1].start_line == 3
        assert blocks[2].start_line == 6

    def test_offset_script_tag_after_blocks(self) -> None:
        """Test offset for script tag appearing after <% %> blocks."""
        content = """<%
Dim x
%>
<html>
<script runat="server">
Function ScriptFunc()
End Function
</script>
</html>"""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        assert len(blocks) == 2
        script_block = next(b for b in blocks if "ScriptFunc" in b.content)
        # <script> starts on line 4
        assert script_block.start_line == 4

    def test_offset_with_inline_expressions_interspersed(self) -> None:
        """Test that inline expressions don't affect offset calculation."""
        content = """<html>
<p><%= Value1 %></p>
<%
Function First()
End Function
%>
<p><%= Value2 %></p>
<%
Function Second()
End Function
%>"""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        # Only code blocks, not inline expressions
        assert len(blocks) == 2
        first = next(b for b in blocks if "First" in b.content)
        second = next(b for b in blocks if "Second" in b.content)
        assert first.start_line == 2
        assert second.start_line == 7

    def test_block_start_line_tracks_delimiter(self) -> None:
        """Test that start_line tracks the delimiter line."""
        content = """<html>
<%
Dim x
%>
</html>"""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        assert len(blocks) == 1
        block = blocks[0]
        # Block delimiter starts at line 1 (0-indexed)
        assert block.start_line == 1
        # Content should contain the code
        assert "Dim x" in block.content


@pytest.mark.vbscript
class TestASPComplexScenarios:
    """Test complex real-world ASP scenarios."""

    def test_include_directive_style(self) -> None:
        """Test handling of include directive patterns."""
        content = """<!--#include file="header.inc"-->
<%
Function MainCode()
End Function
%>
<!--#include file="footer.inc"-->"""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        assert len(blocks) == 1
        assert "MainCode" in blocks[0].content

    def test_asp_directive_not_extracted(self) -> None:
        """Test that ASP directives are handled separately."""
        content = """<%@ Language="VBScript" CodePage="65001" %>
<%
Function RealCode()
End Function
%>"""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        # Should extract both the directive and the code block
        assert len(blocks) >= 1
        code_block = next((b for b in blocks if "RealCode" in b.content), None)
        assert code_block is not None

    def test_deeply_nested_html_structure(self) -> None:
        """Test extraction from deeply nested HTML."""
        content = """<html>
<head>
<title>Test</title>
</head>
<body>
<div class="container">
<div class="row">
<div class="col">
<%
Function DeepNested()
End Function
%>
</div>
</div>
</div>
</body>
</html>"""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        assert len(blocks) == 1
        assert "DeepNested" in blocks[0].content
        assert blocks[0].start_line == 8

    def test_response_write_with_html_tags(self) -> None:
        """Test code containing Response.Write with HTML that looks like tags."""
        content = """<%
Response.Write "<%-- not a block --%>"
Response.Write "<script>alert('hi')</script>"
%>"""
        extractor = ASPScriptExtractor()
        blocks = extractor.extract(content)

        # Should extract the whole thing as one block
        assert len(blocks) == 1
        assert "Response.Write" in blocks[0].content
