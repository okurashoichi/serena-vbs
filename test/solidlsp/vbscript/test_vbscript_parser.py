"""
Unit tests for VBScript parser.

Tests the extraction of Function, Sub, and related symbols from VBScript source code.
"""

import pytest

from solidlsp.language_servers.vbscript_lsp.parser import VBScriptParser, ParsedSymbol


@pytest.mark.vbscript
class TestVBScriptParserFunctions:
    """Test Function extraction from VBScript code."""

    def test_extract_simple_function(self) -> None:
        """Test extraction of a simple function without modifiers."""
        code = """Function GetValue()
    GetValue = 42
End Function
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 1
        func = symbols[0]
        assert func.name == "GetValue"
        assert func.kind == 12  # SymbolKind.Function
        assert func.range.start.line == 0  # 0-indexed, first line after opening """

    def test_extract_public_function(self) -> None:
        """Test extraction of a public function."""
        code = """
Public Function Calculate(x, y)
    Calculate = x + y
End Function
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 1
        func = symbols[0]
        assert func.name == "Calculate"
        assert func.kind == 12

    def test_extract_private_function(self) -> None:
        """Test extraction of a private function."""
        code = """
Private Function InternalHelper()
    InternalHelper = "helper"
End Function
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 1
        func = symbols[0]
        assert func.name == "InternalHelper"
        assert func.kind == 12

    def test_extract_multiple_functions(self) -> None:
        """Test extraction of multiple functions."""
        code = """
Function First()
    First = 1
End Function

Function Second()
    Second = 2
End Function

Public Function Third()
    Third = 3
End Function
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 3
        names = [s.name for s in symbols]
        assert "First" in names
        assert "Second" in names
        assert "Third" in names


@pytest.mark.vbscript
class TestVBScriptParserSubs:
    """Test Sub extraction from VBScript code."""

    def test_extract_simple_sub(self) -> None:
        """Test extraction of a simple Sub without modifiers."""
        code = """
Sub DoSomething()
    MsgBox "Hello"
End Sub
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 1
        sub = symbols[0]
        assert sub.name == "DoSomething"
        assert sub.kind == 12  # Sub uses SymbolKind.Function in LSP

    def test_extract_public_sub(self) -> None:
        """Test extraction of a public Sub."""
        code = """
Public Sub Initialize()
    ' Initialize code
End Sub
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 1
        sub = symbols[0]
        assert sub.name == "Initialize"

    def test_extract_private_sub(self) -> None:
        """Test extraction of a private Sub."""
        code = """
Private Sub Cleanup()
    ' Cleanup code
End Sub
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 1
        sub = symbols[0]
        assert sub.name == "Cleanup"

    def test_extract_sub_with_parameters(self) -> None:
        """Test extraction of a Sub with parameters."""
        code = """
Sub ProcessData(data, options)
    ' Process data
End Sub
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 1
        sub = symbols[0]
        assert sub.name == "ProcessData"


@pytest.mark.vbscript
class TestVBScriptParserCaseInsensitive:
    """Test case-insensitive parsing of VBScript."""

    def test_function_lowercase(self) -> None:
        """Test that lowercase 'function' is recognized."""
        code = """
function lowercase_func()
    lowercase_func = 1
end function
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 1
        assert symbols[0].name == "lowercase_func"

    def test_function_uppercase(self) -> None:
        """Test that uppercase 'FUNCTION' is recognized."""
        code = """
FUNCTION UPPERCASE_FUNC()
    UPPERCASE_FUNC = 1
END FUNCTION
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 1
        assert symbols[0].name == "UPPERCASE_FUNC"

    def test_function_mixed_case(self) -> None:
        """Test that mixed case 'FuNcTiOn' is recognized."""
        code = """
FuNcTiOn MixedCase_Func()
    MixedCase_Func = 1
EnD FuNcTiOn
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 1
        assert symbols[0].name == "MixedCase_Func"

    def test_sub_various_cases(self) -> None:
        """Test that Sub is recognized in various cases."""
        code = """
sub lower_sub()
end sub

SUB UPPER_SUB()
END SUB

Sub Normal_Sub()
End Sub
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 3
        names = [s.name for s in symbols]
        assert "lower_sub" in names
        assert "UPPER_SUB" in names
        assert "Normal_Sub" in names


@pytest.mark.vbscript
class TestVBScriptParserPositionTracking:
    """Test that symbol positions are correctly tracked."""

    def test_function_position(self) -> None:
        """Test that function position is correctly calculated."""
        # Using raw string concatenation to control exact content
        code = (
            "Function FirstFunc()\n"
            "    FirstFunc = 1\n"
            "End Function\n"
            "\n"  # Line 3: blank line
            "Function SecondFunc()\n"  # Line 4
            "    SecondFunc = 2\n"
            "End Function\n"
        )
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 2

        first = next(s for s in symbols if s.name == "FirstFunc")
        assert first.range.start.line == 0  # First line (0-indexed)

        second = next(s for s in symbols if s.name == "SecondFunc")
        # Line 0: Function FirstFunc()
        # Line 1:     FirstFunc = 1
        # Line 2: End Function
        # Line 3: (blank)
        # Line 4: Function SecondFunc()
        assert second.range.start.line == 4  # After blank line

    def test_symbol_has_selection_range(self) -> None:
        """Test that symbols have proper selection ranges."""
        code = """
Function TestFunc()
    TestFunc = 1
End Function
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 1
        func = symbols[0]
        assert func.selection_range is not None
        # Selection range should cover just the function name
        assert func.selection_range.start.line == func.range.start.line


@pytest.mark.vbscript
class TestVBScriptParserMixedContent:
    """Test parsing code with mixed Function and Sub definitions."""

    def test_mixed_functions_and_subs(self) -> None:
        """Test extraction of mixed Function and Sub definitions."""
        code = """
Function GetData()
    GetData = "data"
End Function

Sub ProcessData()
    ' Process
End Sub

Private Function Helper()
    Helper = True
End Function

Public Sub Execute()
    ' Execute
End Sub
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 4
        names = [s.name for s in symbols]
        assert "GetData" in names
        assert "ProcessData" in names
        assert "Helper" in names
        assert "Execute" in names


@pytest.mark.vbscript
class TestVBScriptParserEdgeCases:
    """Test edge cases and robustness."""

    def test_empty_code(self) -> None:
        """Test parsing empty code."""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript("")

        assert len(symbols) == 0

    def test_code_with_only_comments(self) -> None:
        """Test parsing code with only comments."""
        code = """
' This is a comment
' Another comment
' No functions here
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 0

    def test_function_with_inline_comment(self) -> None:
        """Test function with inline comment."""
        code = """
Function GetValue() ' Returns the value
    GetValue = 42
End Function
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 1
        assert symbols[0].name == "GetValue"

    def test_function_with_leading_whitespace(self) -> None:
        """Test function with leading whitespace."""
        code = """
    Function IndentedFunc()
        IndentedFunc = 1
    End Function
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 1
        assert symbols[0].name == "IndentedFunc"


@pytest.mark.vbscript
class TestVBScriptParserRobustness:
    """Test parser robustness with invalid or edge-case syntax."""

    def test_incomplete_function_no_end(self) -> None:
        """Test parsing function without End Function."""
        code = """Function NoEnd()
    NoEnd = 1
' Missing End Function
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        # Should still extract the function (partial match)
        assert len(symbols) >= 0  # Parser should not crash

    def test_incomplete_sub_no_end(self) -> None:
        """Test parsing sub without End Sub."""
        code = """Sub NoEndSub()
    ' Missing End Sub
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        # Parser should not crash
        assert len(symbols) >= 0

    def test_incomplete_class_no_end(self) -> None:
        """Test parsing class without End Class."""
        code = """Class NoEndClass
    ' Missing End Class
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        # Parser should not crash
        assert len(symbols) >= 0

    def test_malformed_function_declaration(self) -> None:
        """Test parsing malformed function declaration."""
        code = """Function ()
    ' Invalid - no name
End Function

Function ValidFunc()
    ValidFunc = 1
End Function
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        # Should still extract valid function
        names = [s.name for s in symbols]
        assert "ValidFunc" in names

    def test_nested_end_statements(self) -> None:
        """Test handling of nested/confusing End statements."""
        code = """Function Outer()
    If True Then
        ' This End If should not close the function
    End If
    Outer = 1
End Function
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 1
        assert symbols[0].name == "Outer"

    def test_string_containing_keywords(self) -> None:
        """Test that keywords in strings don't create false positives."""
        code = '''Function StringTest()
    Dim msg
    msg = "Function End Function Sub End Sub"
    StringTest = msg
End Function
'''
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        # Should only find one function
        assert len(symbols) == 1
        assert symbols[0].name == "StringTest"

    def test_comment_containing_keywords(self) -> None:
        """Test that keywords in comments don't create false positives."""
        code = """' Function FakeFunc() ' This is a comment
' End Function

Function RealFunc()
    ' Sub FakeSub() End Sub
    RealFunc = 1
End Function
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        # Should only find one function
        assert len(symbols) == 1
        assert symbols[0].name == "RealFunc"

    def test_unicode_in_code(self) -> None:
        """Test parsing code with unicode characters."""
        code = """Function GetMessage()
    GetMessage = "こんにちは世界"
End Function
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 1
        assert symbols[0].name == "GetMessage"

    def test_very_long_function_name(self) -> None:
        """Test parsing function with very long name."""
        long_name = "A" * 200
        code = f"""Function {long_name}()
    {long_name} = 1
End Function
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 1
        assert symbols[0].name == long_name

    def test_special_characters_in_parameters(self) -> None:
        """Test function with various parameter styles."""
        code = """Function WithParams(ByVal a, ByRef b, Optional c)
    WithParams = a + b
End Function
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 1
        assert symbols[0].name == "WithParams"

    def test_empty_lines_and_whitespace(self) -> None:
        """Test parsing code with excessive whitespace."""
        code = """


    Function    SpacedFunc   (   )


        SpacedFunc = 1


    End    Function


"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 1
        assert symbols[0].name == "SpacedFunc"


@pytest.mark.vbscript
class TestVBScriptParserClasses:
    """Test Class extraction from VBScript code."""

    def test_extract_simple_class(self) -> None:
        """Test extraction of a simple class."""
        code = """Class MyClass
End Class
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 1
        cls = symbols[0]
        assert cls.name == "MyClass"
        assert cls.kind == 5  # SymbolKind.Class

    def test_extract_class_with_members(self) -> None:
        """Test extraction of a class with member functions."""
        code = """Class Calculator
    Public Function Add(a, b)
        Add = a + b
    End Function

    Private Sub Reset()
        ' Reset state
    End Sub
End Class
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 1
        cls = symbols[0]
        assert cls.name == "Calculator"
        assert cls.kind == 5  # SymbolKind.Class
        assert len(cls.children) == 2

        child_names = [c.name for c in cls.children]
        assert "Add" in child_names
        assert "Reset" in child_names

    def test_extract_multiple_classes(self) -> None:
        """Test extraction of multiple classes."""
        code = """Class FirstClass
End Class

Class SecondClass
End Class
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 2
        names = [s.name for s in symbols]
        assert "FirstClass" in names
        assert "SecondClass" in names

    def test_class_case_insensitive(self) -> None:
        """Test that Class keyword is case-insensitive."""
        code = """CLASS UpperClass
END CLASS

class LowerClass
end class
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 2
        names = [s.name for s in symbols]
        assert "UpperClass" in names
        assert "LowerClass" in names


@pytest.mark.vbscript
class TestVBScriptParserProperties:
    """Test Property extraction from VBScript code."""

    def test_extract_property_get(self) -> None:
        """Test extraction of Property Get."""
        code = """Property Get Value()
    Value = m_Value
End Property
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 1
        prop = symbols[0]
        assert prop.name == "Value"
        assert prop.kind == 7  # SymbolKind.Property

    def test_extract_property_let(self) -> None:
        """Test extraction of Property Let."""
        code = """Property Let Value(newValue)
    m_Value = newValue
End Property
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 1
        prop = symbols[0]
        assert prop.name == "Value"
        assert prop.kind == 7

    def test_extract_property_set(self) -> None:
        """Test extraction of Property Set."""
        code = """Property Set Reference(obj)
    Set m_Ref = obj
End Property
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 1
        prop = symbols[0]
        assert prop.name == "Reference"
        assert prop.kind == 7

    def test_extract_multiple_properties(self) -> None:
        """Test extraction of multiple properties with same name."""
        code = """Property Get Name()
    Name = m_Name
End Property

Property Let Name(value)
    m_Name = value
End Property
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        # Both properties should be extracted
        assert len(symbols) == 2
        assert all(s.name == "Name" for s in symbols)
        assert all(s.kind == 7 for s in symbols)

    def test_property_in_class(self) -> None:
        """Test extraction of properties inside a class."""
        code = """Class Person
    Private m_Name

    Public Property Get Name()
        Name = m_Name
    End Property

    Public Property Let Name(value)
        m_Name = value
    End Property
End Class
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 1
        cls = symbols[0]
        assert cls.name == "Person"
        assert len(cls.children) == 2

        prop_names = [c.name for c in cls.children]
        assert prop_names.count("Name") == 2


@pytest.mark.vbscript
class TestVBScriptParserClassHierarchy:
    """Test hierarchical symbol extraction for classes."""

    def test_class_with_all_member_types(self) -> None:
        """Test class with functions, subs, and properties."""
        code = """Class CompleteClass
    Private m_Value

    Public Function GetValue()
        GetValue = m_Value
    End Function

    Private Sub SetValueInternal(v)
        m_Value = v
    End Sub

    Public Property Get Value()
        Value = m_Value
    End Property

    Public Property Let Value(v)
        m_Value = v
    End Property
End Class
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        assert len(symbols) == 1
        cls = symbols[0]
        assert cls.name == "CompleteClass"
        assert len(cls.children) == 4

        child_names = [c.name for c in cls.children]
        assert "GetValue" in child_names
        assert "SetValueInternal" in child_names
        assert child_names.count("Value") == 2

    def test_nested_classes_not_supported(self) -> None:
        """VBScript doesn't support nested classes, test top-level only."""
        code = """Class Outer
    Public Function Method()
        Method = 1
    End Function
End Class

Class Another
End Class
"""
        parser = VBScriptParser()
        symbols = parser.parse_vbscript(code)

        # Should find both top-level classes
        assert len(symbols) == 2
        outer = next(s for s in symbols if s.name == "Outer")
        assert len(outer.children) == 1
        assert outer.children[0].name == "Method"


@pytest.mark.vbscript
class TestVBScriptParserASPFiles:
    """Test ASP file parsing with position conversion."""

    def test_parse_asp_single_block(self) -> None:
        """Test parsing ASP with a single VBScript block."""
        # Line 0: <html>
        # Line 1: <body>
        # Line 2: <%
        # Line 3: Function GetValue()
        # Line 4:     GetValue = 42
        # Line 5: End Function
        # Line 6: %>
        # Line 7: </body>
        # Line 8: </html>
        content = """<html>
<body>
<%
Function GetValue()
    GetValue = 42
End Function
%>
</body>
</html>"""
        parser = VBScriptParser()
        symbols = parser.parse(content, "test.asp")

        assert len(symbols) == 1
        func = symbols[0]
        assert func.name == "GetValue"
        # Function should be on line 3 of the original ASP file (0-indexed)
        assert func.range.start.line == 3

    def test_parse_asp_multiple_blocks(self) -> None:
        """Test parsing ASP with multiple VBScript blocks."""
        # Line 0: <%
        # Line 1: Dim globalVar
        # Line 2: %>
        # Line 3: <html>
        # Line 4: <%
        # Line 5: Function First()
        # Line 6:     First = 1
        # Line 7: End Function
        # Line 8: %>
        # Line 9: </html>
        content = """<%
Dim globalVar
%>
<html>
<%
Function First()
    First = 1
End Function
%>
</html>"""
        parser = VBScriptParser()
        symbols = parser.parse(content, "page.asp")

        assert len(symbols) == 1
        func = symbols[0]
        assert func.name == "First"
        # Function should be on line 5 of the original ASP file
        assert func.range.start.line == 5

    def test_parse_asp_script_tag(self) -> None:
        """Test parsing ASP with <script runat='server'> tag."""
        # Line 0: <html>
        # Line 1: <script runat="server">
        # Line 2: Sub HandleRequest()
        # Line 3:     ' Handle the request
        # Line 4: End Sub
        # Line 5: </script>
        # Line 6: </html>
        content = """<html>
<script runat="server">
Sub HandleRequest()
    ' Handle the request
End Sub
</script>
</html>"""
        parser = VBScriptParser()
        symbols = parser.parse(content, "page.asp")

        assert len(symbols) == 1
        sub = symbols[0]
        assert sub.name == "HandleRequest"
        # Sub should be on line 2 of the original ASP file
        assert sub.range.start.line == 2

    def test_parse_asp_mixed_blocks_and_script_tags(self) -> None:
        """Test parsing ASP with both <% %> blocks and <script> tags."""
        content = """<%
Function InBlock()
    InBlock = 1
End Function
%>
<html>
<script runat="server">
Function InScript()
    InScript = 2
End Function
</script>
</html>"""
        parser = VBScriptParser()
        symbols = parser.parse(content, "mixed.asp")

        assert len(symbols) == 2
        names = [s.name for s in symbols]
        assert "InBlock" in names
        assert "InScript" in names

        # Verify positions are sorted and correct
        in_block = next(s for s in symbols if s.name == "InBlock")
        in_script = next(s for s in symbols if s.name == "InScript")

        # InBlock is on line 1 (inside <% %> starting at line 0)
        assert in_block.range.start.line == 1
        # InScript is on line 7 (inside <script> starting at line 6)
        assert in_script.range.start.line == 7

    def test_parse_asp_class_with_members(self) -> None:
        """Test parsing ASP with a class definition."""
        content = """<html>
<%
Class MyClass
    Public Function GetValue()
        GetValue = 42
    End Function
End Class
%>
</html>"""
        parser = VBScriptParser()
        symbols = parser.parse(content, "class.asp")

        assert len(symbols) == 1
        cls = symbols[0]
        assert cls.name == "MyClass"
        # Class should be on line 2 of the original ASP file
        assert cls.range.start.line == 2
        assert len(cls.children) == 1
        assert cls.children[0].name == "GetValue"
        # Child function should be on line 3
        assert cls.children[0].range.start.line == 3

    def test_parse_asp_excludes_inline_expressions(self) -> None:
        """Test that <%= %> inline expressions don't produce symbols."""
        content = """<html>
<p><%= GetValue() %></p>
<%
Function GetValue()
    GetValue = 42
End Function
%>
</html>"""
        parser = VBScriptParser()
        symbols = parser.parse(content, "inline.asp")

        # Only the function should be extracted, not the inline expression
        assert len(symbols) == 1
        assert symbols[0].name == "GetValue"

    def test_parse_asp_empty_blocks(self) -> None:
        """Test parsing ASP with empty VBScript blocks."""
        content = """<html>
<% %>
<%
Function OnlyFunc()
    OnlyFunc = 1
End Function
%>
</html>"""
        parser = VBScriptParser()
        symbols = parser.parse(content, "empty.asp")

        # Only the function should be found
        assert len(symbols) == 1
        assert symbols[0].name == "OnlyFunc"

    def test_parse_asp_no_vbscript(self) -> None:
        """Test parsing ASP with no VBScript blocks."""
        content = """<html>
<body>
<p>Plain HTML</p>
</body>
</html>"""
        parser = VBScriptParser()
        symbols = parser.parse(content, "plain.asp")

        assert len(symbols) == 0
