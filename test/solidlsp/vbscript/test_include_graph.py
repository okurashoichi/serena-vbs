"""
Unit tests for VBScript Include Graph.

Tests the IncludeEdge dataclass and IncludeGraph class for managing
file include relationships in VBScript/ASP projects.
"""

import pytest

from solidlsp.language_servers.vbscript_lsp.include_directive import IncludeDirective
from solidlsp.language_servers.vbscript_lsp.include_graph import IncludeEdge, IncludeGraph


@pytest.mark.vbscript
class TestIncludeEdgeCreation:
    """Test IncludeEdge data class creation."""

    def test_include_edge_creation(self) -> None:
        """Test IncludeEdge can be created with required fields."""
        directive = IncludeDirective(
            include_type="file",
            raw_path="utils.asp",
            resolved_uri="file:///project/utils.asp",
            line=5,
            character=0,
            end_line=5,
            end_character=35,
            is_valid=True,
        )
        edge = IncludeEdge(
            source_uri="file:///project/main.asp",
            target_uri="file:///project/utils.asp",
            directive=directive,
        )

        assert edge.source_uri == "file:///project/main.asp"
        assert edge.target_uri == "file:///project/utils.asp"
        assert edge.directive == directive

    def test_include_edge_equality(self) -> None:
        """Test IncludeEdge equality."""
        directive = IncludeDirective(
            include_type="file",
            raw_path="utils.asp",
            resolved_uri="file:///project/utils.asp",
            line=5,
            character=0,
            end_line=5,
            end_character=35,
            is_valid=True,
        )
        edge1 = IncludeEdge(
            source_uri="file:///project/main.asp",
            target_uri="file:///project/utils.asp",
            directive=directive,
        )
        edge2 = IncludeEdge(
            source_uri="file:///project/main.asp",
            target_uri="file:///project/utils.asp",
            directive=directive,
        )

        assert edge1 == edge2


@pytest.mark.vbscript
class TestIncludeGraphBasicStructure:
    """Test IncludeGraph basic data structure."""

    def test_graph_initialization(self) -> None:
        """Test IncludeGraph can be initialized."""
        graph = IncludeGraph()

        # Should start empty
        assert graph.get_direct_includes("file:///any.asp") == []

    def test_graph_clear(self) -> None:
        """Test IncludeGraph can be cleared."""
        graph = IncludeGraph()

        # Add some data
        directive = IncludeDirective(
            include_type="file",
            raw_path="utils.asp",
            resolved_uri="file:///project/utils.asp",
            line=0,
            character=0,
            end_line=0,
            end_character=30,
            is_valid=True,
        )
        graph.update("file:///project/main.asp", [directive])

        # Clear
        graph.clear()

        # Should be empty again
        assert graph.get_direct_includes("file:///project/main.asp") == []


@pytest.mark.vbscript
class TestIncludeGraphUpdate:
    """Test IncludeGraph update method."""

    def test_update_single_include(self) -> None:
        """Test updating with a single include directive."""
        graph = IncludeGraph()

        directive = IncludeDirective(
            include_type="file",
            raw_path="utils.asp",
            resolved_uri="file:///project/utils.asp",
            line=0,
            character=0,
            end_line=0,
            end_character=30,
            is_valid=True,
        )

        affected = graph.update("file:///project/main.asp", [directive])

        # Should return affected URIs
        assert "file:///project/main.asp" in affected

        # Should be able to get direct includes
        includes = graph.get_direct_includes("file:///project/main.asp")
        assert "file:///project/utils.asp" in includes

    def test_update_multiple_includes(self) -> None:
        """Test updating with multiple include directives."""
        graph = IncludeGraph()

        directives = [
            IncludeDirective(
                include_type="file",
                raw_path="header.asp",
                resolved_uri="file:///project/header.asp",
                line=0,
                character=0,
                end_line=0,
                end_character=30,
                is_valid=True,
            ),
            IncludeDirective(
                include_type="file",
                raw_path="utils.asp",
                resolved_uri="file:///project/utils.asp",
                line=1,
                character=0,
                end_line=1,
                end_character=30,
                is_valid=True,
            ),
        ]

        graph.update("file:///project/main.asp", directives)

        includes = graph.get_direct_includes("file:///project/main.asp")
        assert len(includes) == 2
        assert "file:///project/header.asp" in includes
        assert "file:///project/utils.asp" in includes

    def test_update_replaces_existing(self) -> None:
        """Test that update replaces existing includes."""
        graph = IncludeGraph()

        # First update
        directive1 = IncludeDirective(
            include_type="file",
            raw_path="old.asp",
            resolved_uri="file:///project/old.asp",
            line=0,
            character=0,
            end_line=0,
            end_character=30,
            is_valid=True,
        )
        graph.update("file:///project/main.asp", [directive1])

        # Second update with different include
        directive2 = IncludeDirective(
            include_type="file",
            raw_path="new.asp",
            resolved_uri="file:///project/new.asp",
            line=0,
            character=0,
            end_line=0,
            end_character=30,
            is_valid=True,
        )
        graph.update("file:///project/main.asp", [directive2])

        includes = graph.get_direct_includes("file:///project/main.asp")
        assert len(includes) == 1
        assert "file:///project/new.asp" in includes
        assert "file:///project/old.asp" not in includes

    def test_update_skips_invalid_directives(self) -> None:
        """Test that invalid directives are not added to graph edges."""
        graph = IncludeGraph()

        directives = [
            IncludeDirective(
                include_type="file",
                raw_path="valid.asp",
                resolved_uri="file:///project/valid.asp",
                line=0,
                character=0,
                end_line=0,
                end_character=30,
                is_valid=True,
            ),
            IncludeDirective(
                include_type="file",
                raw_path="invalid.asp",
                resolved_uri=None,
                line=1,
                character=0,
                end_line=1,
                end_character=30,
                is_valid=False,
                error_message="File not found",
            ),
        ]

        graph.update("file:///project/main.asp", directives)

        includes = graph.get_direct_includes("file:///project/main.asp")
        assert len(includes) == 1
        assert "file:///project/valid.asp" in includes


@pytest.mark.vbscript
class TestIncludeGraphRemove:
    """Test IncludeGraph remove method."""

    def test_remove_existing_node(self) -> None:
        """Test removing an existing node from the graph."""
        graph = IncludeGraph()

        directive = IncludeDirective(
            include_type="file",
            raw_path="utils.asp",
            resolved_uri="file:///project/utils.asp",
            line=0,
            character=0,
            end_line=0,
            end_character=30,
            is_valid=True,
        )
        graph.update("file:///project/main.asp", [directive])

        affected = graph.remove("file:///project/main.asp")

        # Should return affected URIs
        assert "file:///project/main.asp" in affected

        # Should no longer have includes
        includes = graph.get_direct_includes("file:///project/main.asp")
        assert includes == []

    def test_remove_nonexistent_node(self) -> None:
        """Test removing a non-existent node."""
        graph = IncludeGraph()

        # Should not raise an error
        affected = graph.remove("file:///nonexistent.asp")
        assert affected == []

    def test_remove_updates_reverse_index(self) -> None:
        """Test that remove updates the reverse index correctly."""
        graph = IncludeGraph()

        # main.asp includes utils.asp
        directive = IncludeDirective(
            include_type="file",
            raw_path="utils.asp",
            resolved_uri="file:///project/utils.asp",
            line=0,
            character=0,
            end_line=0,
            end_character=30,
            is_valid=True,
        )
        graph.update("file:///project/main.asp", [directive])

        # Verify reverse index before removal
        includers = graph.get_includers("file:///project/utils.asp")
        assert "file:///project/main.asp" in includers

        # Remove main.asp
        graph.remove("file:///project/main.asp")

        # Reverse index should be updated
        includers = graph.get_includers("file:///project/utils.asp")
        assert "file:///project/main.asp" not in includers


@pytest.mark.vbscript
class TestIncludeGraphGetDirectIncludes:
    """Test IncludeGraph get_direct_includes method."""

    def test_get_direct_includes_empty(self) -> None:
        """Test getting direct includes for a file with no includes."""
        graph = IncludeGraph()

        includes = graph.get_direct_includes("file:///project/main.asp")
        assert includes == []

    def test_get_direct_includes_single(self) -> None:
        """Test getting direct includes for a file with one include."""
        graph = IncludeGraph()

        directive = IncludeDirective(
            include_type="file",
            raw_path="utils.asp",
            resolved_uri="file:///project/utils.asp",
            line=0,
            character=0,
            end_line=0,
            end_character=30,
            is_valid=True,
        )
        graph.update("file:///project/main.asp", [directive])

        includes = graph.get_direct_includes("file:///project/main.asp")
        assert includes == ["file:///project/utils.asp"]

    def test_get_direct_includes_multiple(self) -> None:
        """Test getting direct includes for a file with multiple includes."""
        graph = IncludeGraph()

        directives = [
            IncludeDirective(
                include_type="file",
                raw_path="a.asp",
                resolved_uri="file:///project/a.asp",
                line=0,
                character=0,
                end_line=0,
                end_character=30,
                is_valid=True,
            ),
            IncludeDirective(
                include_type="file",
                raw_path="b.asp",
                resolved_uri="file:///project/b.asp",
                line=1,
                character=0,
                end_line=1,
                end_character=30,
                is_valid=True,
            ),
        ]
        graph.update("file:///project/main.asp", directives)

        includes = graph.get_direct_includes("file:///project/main.asp")
        assert len(includes) == 2
        assert "file:///project/a.asp" in includes
        assert "file:///project/b.asp" in includes


@pytest.mark.vbscript
class TestIncludeGraphGetIncluders:
    """Test IncludeGraph get_includers method (reverse lookup)."""

    def test_get_includers_empty(self) -> None:
        """Test getting includers for a file not included by anyone."""
        graph = IncludeGraph()

        includers = graph.get_includers("file:///project/orphan.asp")
        assert includers == []

    def test_get_includers_single(self) -> None:
        """Test getting includers when included by one file."""
        graph = IncludeGraph()

        directive = IncludeDirective(
            include_type="file",
            raw_path="utils.asp",
            resolved_uri="file:///project/utils.asp",
            line=0,
            character=0,
            end_line=0,
            end_character=30,
            is_valid=True,
        )
        graph.update("file:///project/main.asp", [directive])

        includers = graph.get_includers("file:///project/utils.asp")
        assert includers == ["file:///project/main.asp"]

    def test_get_includers_multiple(self) -> None:
        """Test getting includers when included by multiple files."""
        graph = IncludeGraph()

        # Both page1.asp and page2.asp include utils.asp
        directive = IncludeDirective(
            include_type="file",
            raw_path="utils.asp",
            resolved_uri="file:///project/utils.asp",
            line=0,
            character=0,
            end_line=0,
            end_character=30,
            is_valid=True,
        )
        graph.update("file:///project/page1.asp", [directive])
        graph.update("file:///project/page2.asp", [directive])

        includers = graph.get_includers("file:///project/utils.asp")
        assert len(includers) == 2
        assert "file:///project/page1.asp" in includers
        assert "file:///project/page2.asp" in includers


@pytest.mark.vbscript
class TestIncludeGraphGetIncludeDirectives:
    """Test IncludeGraph get_include_directives method."""

    def test_get_include_directives_empty(self) -> None:
        """Test getting directives for a file with no includes."""
        graph = IncludeGraph()

        directives = graph.get_include_directives("file:///project/main.asp")
        assert directives == []

    def test_get_include_directives_returns_all(self) -> None:
        """Test getting directives returns all including invalid ones."""
        graph = IncludeGraph()

        directives = [
            IncludeDirective(
                include_type="file",
                raw_path="valid.asp",
                resolved_uri="file:///project/valid.asp",
                line=0,
                character=0,
                end_line=0,
                end_character=30,
                is_valid=True,
            ),
            IncludeDirective(
                include_type="file",
                raw_path="invalid.asp",
                resolved_uri=None,
                line=1,
                character=0,
                end_line=1,
                end_character=30,
                is_valid=False,
                error_message="File not found",
            ),
        ]
        graph.update("file:///project/main.asp", directives)

        # Should return all directives for Document Symbols display
        result = graph.get_include_directives("file:///project/main.asp")
        assert len(result) == 2
        assert result[0].raw_path == "valid.asp"
        assert result[1].raw_path == "invalid.asp"


def _make_directive(raw_path: str, resolved_uri: str) -> IncludeDirective:
    """Helper to create a valid IncludeDirective."""
    return IncludeDirective(
        include_type="file",
        raw_path=raw_path,
        resolved_uri=resolved_uri,
        line=0,
        character=0,
        end_line=0,
        end_character=30,
        is_valid=True,
    )


@pytest.mark.vbscript
class TestIncludeGraphTransitiveIncludes:
    """Test IncludeGraph get_transitive_includes method."""

    def test_transitive_includes_empty(self) -> None:
        """Test transitive includes for a file with no includes."""
        graph = IncludeGraph()

        result = graph.get_transitive_includes("file:///project/main.asp")
        assert result == []

    def test_transitive_includes_single_level(self) -> None:
        """Test transitive includes with single level (A -> B)."""
        graph = IncludeGraph()

        # main.asp includes utils.asp
        graph.update(
            "file:///project/main.asp",
            [_make_directive("utils.asp", "file:///project/utils.asp")],
        )

        result = graph.get_transitive_includes("file:///project/main.asp")
        assert result == ["file:///project/utils.asp"]

    def test_transitive_includes_two_levels(self) -> None:
        """Test transitive includes with two levels (A -> B -> C)."""
        graph = IncludeGraph()

        # main.asp includes utils.asp
        graph.update(
            "file:///project/main.asp",
            [_make_directive("utils.asp", "file:///project/utils.asp")],
        )
        # utils.asp includes common.asp
        graph.update(
            "file:///project/utils.asp",
            [_make_directive("common.asp", "file:///project/common.asp")],
        )

        result = graph.get_transitive_includes("file:///project/main.asp")
        assert len(result) == 2
        assert "file:///project/utils.asp" in result
        assert "file:///project/common.asp" in result

    def test_transitive_includes_multiple_branches(self) -> None:
        """Test transitive includes with multiple branches."""
        graph = IncludeGraph()

        # main.asp includes both header.asp and utils.asp
        graph.update(
            "file:///project/main.asp",
            [
                _make_directive("header.asp", "file:///project/header.asp"),
                _make_directive("utils.asp", "file:///project/utils.asp"),
            ],
        )
        # header.asp includes common.asp
        graph.update(
            "file:///project/header.asp",
            [_make_directive("common.asp", "file:///project/common.asp")],
        )

        result = graph.get_transitive_includes("file:///project/main.asp")
        assert len(result) == 3
        assert "file:///project/header.asp" in result
        assert "file:///project/utils.asp" in result
        assert "file:///project/common.asp" in result

    def test_transitive_includes_shared_dependency(self) -> None:
        """Test transitive includes with shared dependency (diamond pattern)."""
        graph = IncludeGraph()

        # main.asp includes both a.asp and b.asp
        graph.update(
            "file:///project/main.asp",
            [
                _make_directive("a.asp", "file:///project/a.asp"),
                _make_directive("b.asp", "file:///project/b.asp"),
            ],
        )
        # Both a.asp and b.asp include common.asp
        graph.update(
            "file:///project/a.asp",
            [_make_directive("common.asp", "file:///project/common.asp")],
        )
        graph.update(
            "file:///project/b.asp",
            [_make_directive("common.asp", "file:///project/common.asp")],
        )

        result = graph.get_transitive_includes("file:///project/main.asp")
        # common.asp should appear only once
        assert len(result) == 3
        assert result.count("file:///project/common.asp") == 1


@pytest.mark.vbscript
class TestIncludeGraphCycleDetection:
    """Test IncludeGraph cycle detection."""

    def test_has_cycle_no_cycle(self) -> None:
        """Test has_cycle returns False when no cycle exists."""
        graph = IncludeGraph()

        # Linear chain: A -> B -> C
        graph.update(
            "file:///project/a.asp",
            [_make_directive("b.asp", "file:///project/b.asp")],
        )
        graph.update(
            "file:///project/b.asp",
            [_make_directive("c.asp", "file:///project/c.asp")],
        )

        assert graph.has_cycle("file:///project/a.asp") is False

    def test_has_cycle_self_reference(self) -> None:
        """Test has_cycle detects self-referencing cycle."""
        graph = IncludeGraph()

        # A includes itself
        graph.update(
            "file:///project/a.asp",
            [_make_directive("a.asp", "file:///project/a.asp")],
        )

        assert graph.has_cycle("file:///project/a.asp") is True

    def test_has_cycle_simple_cycle(self) -> None:
        """Test has_cycle detects simple two-node cycle."""
        graph = IncludeGraph()

        # A -> B -> A
        graph.update(
            "file:///project/a.asp",
            [_make_directive("b.asp", "file:///project/b.asp")],
        )
        graph.update(
            "file:///project/b.asp",
            [_make_directive("a.asp", "file:///project/a.asp")],
        )

        assert graph.has_cycle("file:///project/a.asp") is True
        assert graph.has_cycle("file:///project/b.asp") is True

    def test_has_cycle_longer_cycle(self) -> None:
        """Test has_cycle detects longer cycle (A -> B -> C -> A)."""
        graph = IncludeGraph()

        graph.update(
            "file:///project/a.asp",
            [_make_directive("b.asp", "file:///project/b.asp")],
        )
        graph.update(
            "file:///project/b.asp",
            [_make_directive("c.asp", "file:///project/c.asp")],
        )
        graph.update(
            "file:///project/c.asp",
            [_make_directive("a.asp", "file:///project/a.asp")],
        )

        assert graph.has_cycle("file:///project/a.asp") is True

    def test_transitive_includes_with_cycle(self) -> None:
        """Test transitive includes handles cycles without infinite loop."""
        graph = IncludeGraph()

        # A -> B -> C -> A (cycle)
        graph.update(
            "file:///project/a.asp",
            [_make_directive("b.asp", "file:///project/b.asp")],
        )
        graph.update(
            "file:///project/b.asp",
            [_make_directive("c.asp", "file:///project/c.asp")],
        )
        graph.update(
            "file:///project/c.asp",
            [_make_directive("a.asp", "file:///project/a.asp")],
        )

        # Should return reachable nodes without infinite loop
        # a.asp (the start node) is excluded from results as it's the source
        result = graph.get_transitive_includes("file:///project/a.asp")
        assert len(result) == 2
        assert "file:///project/b.asp" in result
        assert "file:///project/c.asp" in result
        # The key is that it doesn't cause an infinite loop

    def test_has_cycle_no_cycle_from_node(self) -> None:
        """Test has_cycle from a node not in a cycle returns False."""
        graph = IncludeGraph()

        # A -> B, C -> D -> C (cycle only in C-D)
        graph.update(
            "file:///project/a.asp",
            [_make_directive("b.asp", "file:///project/b.asp")],
        )
        graph.update(
            "file:///project/c.asp",
            [_make_directive("d.asp", "file:///project/d.asp")],
        )
        graph.update(
            "file:///project/d.asp",
            [_make_directive("c.asp", "file:///project/c.asp")],
        )

        # A is not part of any cycle
        assert graph.has_cycle("file:///project/a.asp") is False
        # C and D are in a cycle
        assert graph.has_cycle("file:///project/c.asp") is True
