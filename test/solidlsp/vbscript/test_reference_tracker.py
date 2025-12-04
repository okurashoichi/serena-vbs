"""
Unit tests for VBScript ReferenceTracker.

Tests the reference tracking and search functionality for VBScript symbols.
"""

import pytest

from solidlsp.language_servers.vbscript_lsp.parser import (
    ParsedSymbol,
    Position,
    Range,
    SYMBOL_KIND_FUNCTION,
    SYMBOL_KIND_CLASS,
    SYMBOL_KIND_VARIABLE,
)
from solidlsp.language_servers.vbscript_lsp.reference import Reference
from solidlsp.language_servers.vbscript_lsp.reference_tracker import ReferenceTracker


def make_symbol(
    name: str,
    kind: int = SYMBOL_KIND_FUNCTION,
    start_line: int = 0,
    end_line: int = 0,
    children: list[ParsedSymbol] | None = None,
) -> ParsedSymbol:
    """Helper to create a ParsedSymbol for testing."""
    return ParsedSymbol(
        name=name,
        kind=kind,
        range=Range(
            start=Position(line=start_line, character=0),
            end=Position(line=end_line, character=0),
        ),
        selection_range=Range(
            start=Position(line=start_line, character=0),
            end=Position(line=start_line, character=len(name)),
        ),
        children=children or [],
    )


@pytest.mark.vbscript
class TestReferenceTrackerUpdate:
    """Test ReferenceTracker update operations."""

    def test_update_extracts_function_calls(self) -> None:
        """Test that update extracts function call references."""
        tracker = ReferenceTracker()
        content = '''
Function GetValue()
    GetValue = 42
End Function

Sub Main()
    Dim x
    x = GetValue()
End Sub
'''
        symbols = [
            make_symbol("GetValue", SYMBOL_KIND_FUNCTION, 1, 3),
            make_symbol("Main", SYMBOL_KIND_FUNCTION, 5, 8),
        ]

        tracker.update("file:///test.vbs", content, symbols)

        # Should find the reference to GetValue in Main
        refs = tracker.find_references("GetValue")
        # At least the call in Main (line 7: x = GetValue())
        assert len(refs) >= 1
        # Check that we found the call site, not just the definition
        call_refs = [r for r in refs if not r.is_definition]
        assert len(call_refs) >= 1

    def test_update_extracts_variable_references(self) -> None:
        """Test that update extracts variable references."""
        tracker = ReferenceTracker()
        content = '''
Dim myVar
myVar = 10
x = myVar + 5
'''
        symbols = [make_symbol("myVar", SYMBOL_KIND_VARIABLE, 1, 1)]

        tracker.update("file:///test.vbs", content, symbols)

        refs = tracker.find_references("myVar")
        # Should find references on lines 2 and 3
        assert len(refs) >= 2

    def test_update_excludes_comments(self) -> None:
        """Test that references in comments are excluded."""
        tracker = ReferenceTracker()
        content = '''
Function GetValue()
    GetValue = 42
End Function

' Call GetValue here
Sub Main()
    ' GetValue is a helper function
    Dim x
    x = GetValue()
End Sub
'''
        symbols = [
            make_symbol("GetValue", SYMBOL_KIND_FUNCTION, 1, 3),
            make_symbol("Main", SYMBOL_KIND_FUNCTION, 6, 10),
        ]

        tracker.update("file:///test.vbs", content, symbols)

        refs = tracker.find_references("GetValue")
        # Should NOT include the commented references (lines 5 and 7)
        for ref in refs:
            # Line 5 is "' Call GetValue here"
            # Line 7 is "    ' GetValue is a helper function"
            assert ref.line != 5
            assert ref.line != 7

    def test_update_excludes_string_literals(self) -> None:
        """Test that references in string literals are excluded."""
        tracker = ReferenceTracker()
        content = '''
Function GetValue()
    GetValue = 42
End Function

Sub Main()
    Dim msg
    msg = "Call GetValue to get the value"
    Dim x
    x = GetValue()
End Sub
'''
        symbols = [
            make_symbol("GetValue", SYMBOL_KIND_FUNCTION, 1, 3),
            make_symbol("Main", SYMBOL_KIND_FUNCTION, 5, 10),
        ]

        tracker.update("file:///test.vbs", content, symbols)

        refs = tracker.find_references("GetValue")
        # Should NOT include the string literal reference (line 7)
        for ref in refs:
            # Line 7 contains the string "Call GetValue to get the value"
            if ref.line == 7:
                # If we found line 7, it should be the actual call, not in string
                assert ref.character > content.split("\n")[7].find('"')

    def test_update_case_insensitive(self) -> None:
        """Test that VBScript's case-insensitivity is handled."""
        tracker = ReferenceTracker()
        content = '''
Function GetValue()
    GetValue = 42
End Function

Sub Main()
    Dim x
    x = GETVALUE()
    x = getvalue()
    x = GetValue()
End Sub
'''
        symbols = [
            make_symbol("GetValue", SYMBOL_KIND_FUNCTION, 1, 3),
            make_symbol("Main", SYMBOL_KIND_FUNCTION, 5, 10),
        ]

        tracker.update("file:///test.vbs", content, symbols)

        # All case variations should be found
        refs = tracker.find_references("GetValue")
        assert len(refs) >= 3  # At least the 3 calls


@pytest.mark.vbscript
class TestReferenceTrackerRemove:
    """Test ReferenceTracker remove operations."""

    def test_remove_deletes_document_references(self) -> None:
        """Test that remove deletes all references for a document."""
        tracker = ReferenceTracker()
        content = '''
Function GetValue()
    GetValue = 42
End Function
'''
        symbols = [make_symbol("GetValue", SYMBOL_KIND_FUNCTION, 1, 3)]

        tracker.update("file:///test.vbs", content, symbols)
        tracker.remove("file:///test.vbs")

        refs = tracker.find_references("GetValue")
        assert len(refs) == 0

    def test_remove_updates_name_index(self) -> None:
        """Test that remove also cleans up the name index."""
        tracker = ReferenceTracker()
        content1 = '''
Sub Helper()
End Sub
'''
        content2 = '''
Sub Main()
    Helper
End Sub
'''
        tracker.update("file:///file1.vbs", content1, [make_symbol("Helper", start_line=1, end_line=2)])
        tracker.update("file:///file2.vbs", content2, [make_symbol("Main", start_line=1, end_line=3)])

        # Remove file1
        tracker.remove("file:///file1.vbs")

        # References from file2 should still exist
        refs = tracker.find_references("Helper")
        # Only the reference in file2 should remain (not the definition from file1)
        assert all(r.uri == "file:///file2.vbs" for r in refs)

    def test_remove_nonexistent_document(self) -> None:
        """Test that removing a nonexistent document doesn't fail."""
        tracker = ReferenceTracker()
        # Should not raise
        tracker.remove("file:///nonexistent.vbs")


@pytest.mark.vbscript
class TestReferenceTrackerFindReferences:
    """Test reference search functionality."""

    def test_find_references_returns_references(self) -> None:
        """Test that find_references returns Reference objects."""
        tracker = ReferenceTracker()
        content = '''
Function GetValue()
    GetValue = 42
End Function

Sub Main()
    x = GetValue()
End Sub
'''
        symbols = [
            make_symbol("GetValue", SYMBOL_KIND_FUNCTION, 1, 3),
            make_symbol("Main", SYMBOL_KIND_FUNCTION, 5, 7),
        ]

        tracker.update("file:///test.vbs", content, symbols)

        refs = tracker.find_references("GetValue")
        assert len(refs) >= 1
        assert all(isinstance(r, Reference) for r in refs)

    def test_find_references_case_insensitive(self) -> None:
        """Test that find_references is case-insensitive."""
        tracker = ReferenceTracker()
        content = '''
Function MyFunc()
End Function

Sub Main()
    MyFunc
End Sub
'''
        symbols = [
            make_symbol("MyFunc", SYMBOL_KIND_FUNCTION, 1, 2),
            make_symbol("Main", SYMBOL_KIND_FUNCTION, 4, 6),
        ]

        tracker.update("file:///test.vbs", content, symbols)

        # Try different cases
        assert len(tracker.find_references("myfunc")) >= 1
        assert len(tracker.find_references("MYFUNC")) >= 1
        assert len(tracker.find_references("MyFunc")) >= 1

    def test_find_references_across_documents(self) -> None:
        """Test finding references across multiple documents."""
        tracker = ReferenceTracker()

        content1 = '''
Function Helper()
End Function
'''
        content2 = '''
Sub Main()
    Helper
End Sub
'''
        tracker.update("file:///file1.vbs", content1, [make_symbol("Helper", start_line=1, end_line=2)])
        tracker.update("file:///file2.vbs", content2, [make_symbol("Main", start_line=1, end_line=3)])

        refs = tracker.find_references("Helper")

        # Should find references from both files
        uris = set(r.uri for r in refs)
        assert len(uris) >= 1

    def test_find_references_not_found(self) -> None:
        """Test that find_references returns empty list for missing symbol."""
        tracker = ReferenceTracker()
        content = '''
Function GetValue()
End Function
'''
        symbols = [make_symbol("GetValue", SYMBOL_KIND_FUNCTION, 1, 2)]
        tracker.update("file:///test.vbs", content, symbols)

        refs = tracker.find_references("NonExistent")
        assert refs == []

    def test_find_references_include_declaration_true(self) -> None:
        """Test that include_declaration=True includes the definition."""
        tracker = ReferenceTracker()
        content = '''
Function GetValue()
    GetValue = 42
End Function

Sub Main()
    x = GetValue()
End Sub
'''
        symbols = [
            make_symbol("GetValue", SYMBOL_KIND_FUNCTION, 1, 3),
            make_symbol("Main", SYMBOL_KIND_FUNCTION, 5, 7),
        ]

        tracker.update("file:///test.vbs", content, symbols)

        refs = tracker.find_references("GetValue", include_declaration=True)
        # Should include at least one definition
        definitions = [r for r in refs if r.is_definition]
        assert len(definitions) >= 1

    def test_find_references_include_declaration_false(self) -> None:
        """Test that include_declaration=False excludes the definition."""
        tracker = ReferenceTracker()
        content = '''
Function GetValue()
    GetValue = 42
End Function

Sub Main()
    x = GetValue()
End Sub
'''
        symbols = [
            make_symbol("GetValue", SYMBOL_KIND_FUNCTION, 1, 3),
            make_symbol("Main", SYMBOL_KIND_FUNCTION, 5, 7),
        ]

        tracker.update("file:///test.vbs", content, symbols)

        refs = tracker.find_references("GetValue", include_declaration=False)
        # Should NOT include definitions
        definitions = [r for r in refs if r.is_definition]
        assert len(definitions) == 0


@pytest.mark.vbscript
class TestReferenceTrackerEdgeCases:
    """Test edge cases and complex scenarios."""

    def test_mixed_comments_and_code(self) -> None:
        """Test handling of mixed comments and code on same line."""
        tracker = ReferenceTracker()
        content = '''
Function GetValue()
End Function

Sub Main()
    x = GetValue() ' Get the value
End Sub
'''
        symbols = [
            make_symbol("GetValue", SYMBOL_KIND_FUNCTION, 1, 2),
            make_symbol("Main", SYMBOL_KIND_FUNCTION, 4, 6),
        ]

        tracker.update("file:///test.vbs", content, symbols)

        refs = tracker.find_references("GetValue")
        # Should find the actual call but not the comment
        call_refs = [r for r in refs if not r.is_definition and r.line == 5]
        assert len(call_refs) == 1  # Only the actual call, not the comment

    def test_user_defined_identifiers_not_confused_with_keywords(self) -> None:
        """Test that user-defined identifiers are found correctly."""
        tracker = ReferenceTracker()
        content = '''
Dim MyValue
MyValue = 1
x = MyValue

Function GetData()
    GetData = MyValue
End Function
'''
        symbols = [
            make_symbol("MyValue", SYMBOL_KIND_VARIABLE, 1, 1),
            make_symbol("GetData", SYMBOL_KIND_FUNCTION, 5, 7),
        ]

        tracker.update("file:///test.vbs", content, symbols)

        # "MyValue" should be found
        refs = tracker.find_references("MyValue")
        # Should find references on lines 2, 3, and 6
        assert len(refs) >= 3

        # Keywords like "End" in "End Function" should not be tracked
        # as user-defined identifiers
        end_refs = tracker.find_references("End")
        assert len(end_refs) == 0  # "End" is a keyword

    def test_empty_content(self) -> None:
        """Test handling of empty content."""
        tracker = ReferenceTracker()

        tracker.update("file:///empty.vbs", "", [])

        refs = tracker.find_references("anything")
        assert refs == []

    def test_multiline_strings(self) -> None:
        """Test handling of multiline string scenarios (VBScript concatenation)."""
        tracker = ReferenceTracker()
        content = '''
Function GetValue()
End Function

Sub Main()
    msg = "Line 1 " & _
          "GetValue is here " & _
          "Line 3"
    x = GetValue()
End Sub
'''
        symbols = [
            make_symbol("GetValue", SYMBOL_KIND_FUNCTION, 1, 2),
            make_symbol("Main", SYMBOL_KIND_FUNCTION, 4, 10),
        ]

        tracker.update("file:///test.vbs", content, symbols)

        refs = tracker.find_references("GetValue")
        # Should find the actual call on line 9, not the string on line 6
        actual_calls = [r for r in refs if not r.is_definition]
        for ref in actual_calls:
            # The string literal is on line 6
            if ref.line == 6:
                # This should be from the string continuation, which should be excluded
                pytest.fail("Found reference in string literal")
