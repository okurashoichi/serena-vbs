"""Include Graph for managing ASP file include relationships.

This module provides the IncludeEdge dataclass and IncludeGraph class for
managing the include relationships between ASP/VBScript files. The graph
supports Go to Definition and Find References across included files.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from solidlsp.language_servers.vbscript_lsp.include_directive import IncludeDirective

logger = logging.getLogger(__name__)


@dataclass
class IncludeEdge:
    """Represents an include relationship between two files.

    Attributes:
        source_uri: The URI of the file containing the include directive.
        target_uri: The URI of the included file.
        directive: The parsed include directive.
    """

    source_uri: str
    target_uri: str
    directive: IncludeDirective


class IncludeGraph:
    """Graph for tracking include relationships between ASP files.

    This class maintains a directed graph of include relationships with:
    - Forward edges (URI -> list of included URIs)
    - Reverse edges (URI -> list of including URIs)

    The graph supports queries for direct includes, transitive includes,
    and reverse lookups (who includes a given file).
    """

    def __init__(self) -> None:
        """Initialize an empty include graph."""
        # Forward edges: source_uri -> list of IncludeEdge
        self._edges: dict[str, list[IncludeEdge]] = {}

        # Reverse edges: target_uri -> list of source_uris
        self._reverse_edges: dict[str, list[str]] = {}

        # Store all directives (including invalid ones) for Document Symbols
        self._directives: dict[str, list[IncludeDirective]] = {}

    def update(self, uri: str, directives: list[IncludeDirective]) -> list[str]:
        """Update the include relationships for a file.

        This replaces any existing includes for the given URI.

        Args:
            uri: The URI of the file being updated.
            directives: The parsed include directives from the file.

        Returns:
            A list of affected URIs that may need re-indexing.
        """
        affected: list[str] = [uri]

        # Remove existing edges from this URI
        self._remove_edges_from(uri)

        # Store all directives (for Document Symbols)
        self._directives[uri] = list(directives)

        # Add new edges for valid directives
        edges: list[IncludeEdge] = []
        for directive in directives:
            if directive.is_valid and directive.resolved_uri:
                edge = IncludeEdge(
                    source_uri=uri,
                    target_uri=directive.resolved_uri,
                    directive=directive,
                )
                edges.append(edge)

                # Update reverse index
                if directive.resolved_uri not in self._reverse_edges:
                    self._reverse_edges[directive.resolved_uri] = []
                if uri not in self._reverse_edges[directive.resolved_uri]:
                    self._reverse_edges[directive.resolved_uri].append(uri)

                # Add target to affected list
                if directive.resolved_uri not in affected:
                    affected.append(directive.resolved_uri)

        if edges:
            self._edges[uri] = edges

        return affected

    def remove(self, uri: str) -> list[str]:
        """Remove a file from the include graph.

        Args:
            uri: The URI of the file to remove.

        Returns:
            A list of affected URIs that may need re-indexing.
        """
        if uri not in self._edges and uri not in self._directives:
            return []

        affected: list[str] = [uri]

        # Get targets before removing
        if uri in self._edges:
            for edge in self._edges[uri]:
                if edge.target_uri not in affected:
                    affected.append(edge.target_uri)

        # Remove forward edges
        self._remove_edges_from(uri)

        # Remove stored directives
        if uri in self._directives:
            del self._directives[uri]

        # Remove from reverse edges (if this URI was included by someone)
        if uri in self._reverse_edges:
            del self._reverse_edges[uri]

        return affected

    def clear(self) -> None:
        """Clear all data from the graph."""
        self._edges.clear()
        self._reverse_edges.clear()
        self._directives.clear()

    def get_direct_includes(self, uri: str) -> list[str]:
        """Get the URIs directly included by a file.

        Args:
            uri: The URI of the file.

        Returns:
            A list of URIs that the file directly includes.
        """
        if uri not in self._edges:
            return []

        return [edge.target_uri for edge in self._edges[uri]]

    def get_includers(self, uri: str) -> list[str]:
        """Get the URIs of files that include the given file.

        Args:
            uri: The URI of the file.

        Returns:
            A list of URIs that include the given file.
        """
        return list(self._reverse_edges.get(uri, []))

    def get_include_directives(self, uri: str) -> list[IncludeDirective]:
        """Get all include directives for a file.

        This includes both valid and invalid directives, which is useful
        for displaying in Document Symbols.

        Args:
            uri: The URI of the file.

        Returns:
            A list of IncludeDirective objects.
        """
        return list(self._directives.get(uri, []))

    def get_transitive_includes(self, uri: str) -> list[str]:
        """Get all URIs transitively included by a file.

        This performs a depth-first search to find all files reachable
        through include relationships. Cycles are handled by tracking
        visited nodes.

        Args:
            uri: The URI of the file.

        Returns:
            A list of URIs that are transitively included (in dependency order).
        """
        result: list[str] = []
        visited: set[str] = {uri}  # Start with the source URI as visited

        def dfs(current_uri: str) -> None:
            for target_uri in self.get_direct_includes(current_uri):
                if target_uri not in visited:
                    visited.add(target_uri)
                    result.append(target_uri)
                    dfs(target_uri)

        dfs(uri)
        return result

    def has_cycle(self, uri: str) -> bool:
        """Check if there is a cycle reachable from the given URI.

        This performs a depth-first search looking for back edges that
        would indicate a cycle.

        Args:
            uri: The starting URI to check.

        Returns:
            True if a cycle is detected, False otherwise.
        """
        # Track nodes in the current DFS path (for cycle detection)
        path: set[str] = set()
        # Track all visited nodes (to avoid re-processing)
        visited: set[str] = set()

        def dfs(current_uri: str) -> bool:
            if current_uri in path:
                # Found a back edge - cycle detected
                logger.warning(f"Circular include detected involving: {current_uri}")
                return True

            if current_uri in visited:
                # Already fully processed this node, no cycle through it
                return False

            path.add(current_uri)
            visited.add(current_uri)

            for target_uri in self.get_direct_includes(current_uri):
                if dfs(target_uri):
                    return True

            path.remove(current_uri)
            return False

        return dfs(uri)

    def _remove_edges_from(self, uri: str) -> None:
        """Remove all forward edges from a URI and update reverse index.

        Args:
            uri: The source URI whose edges should be removed.
        """
        if uri not in self._edges:
            return

        # Update reverse index for each target
        for edge in self._edges[uri]:
            target = edge.target_uri
            if target in self._reverse_edges:
                self._reverse_edges[target] = [
                    source for source in self._reverse_edges[target] if source != uri
                ]
                # Clean up empty lists
                if not self._reverse_edges[target]:
                    del self._reverse_edges[target]

        # Remove forward edges
        del self._edges[uri]
