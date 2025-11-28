"""
Graph analytics and traversal algorithms for Claude Code Memory Server.

This module provides advanced graph operations including path finding,
cluster detection, bridge identification, and graph metrics analysis.

Phase 4 Implementation - Advanced Relationship System
"""

from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict, deque
from dataclasses import dataclass
import logging

from .models import (
    Memory,
    Relationship,
    RelationshipType,
    MemoryGraph,
)
from .relationships import RelationshipCategory, relationship_manager

logger = logging.getLogger(__name__)


@dataclass
class GraphPath:
    """
    Represents a path through the memory graph.

    Attributes:
        memories: List of memories in the path (in order)
        relationships: List of relationships connecting the memories
        total_strength: Cumulative strength of all relationships
        length: Number of hops in the path
    """

    memories: List[Memory]
    relationships: List[Relationship]
    total_strength: float
    length: int

    @property
    def average_strength(self) -> float:
        """Calculate average relationship strength along the path."""
        return self.total_strength / self.length if self.length > 0 else 0.0


@dataclass
class MemoryCluster:
    """
    Represents a cluster of related memories.

    Attributes:
        memories: List of memories in the cluster
        internal_relationships: Relationships within the cluster
        density: How densely connected the cluster is (0.0 to 1.0)
        strength: Average relationship strength within cluster
        categories: Relationship categories present in cluster
    """

    memories: List[Memory]
    internal_relationships: List[Relationship]
    density: float
    strength: float
    categories: Set[RelationshipCategory]


@dataclass
class BridgeNode:
    """
    Represents a memory that bridges different clusters.

    Attributes:
        memory: The bridge memory
        connected_clusters: Cluster IDs this memory connects
        bridge_strength: Importance of this bridge (0.0 to 1.0)
    """

    memory: Memory
    connected_clusters: List[int]
    bridge_strength: float


class GraphAnalyzer:
    """
    Provides graph analytics and traversal algorithms.

    This class implements algorithms for analyzing the structure and
    connectivity of the memory graph.
    """

    def __init__(self):
        """Initialize the graph analyzer."""
        self.rel_manager = relationship_manager

    def build_adjacency_lists(
        self,
        memories: List[Memory],
        relationships: List[Relationship]
    ) -> Tuple[Dict[str, List[str]], Dict[Tuple[str, str], Relationship]]:
        """
        Build adjacency list representation of the graph.

        Args:
            memories: List of memory nodes
            relationships: List of relationships (edges)

        Returns:
            Tuple of (adjacency_dict, relationship_map):
                - adjacency_dict: Maps memory_id -> list of connected memory_ids
                - relationship_map: Maps (from_id, to_id) -> Relationship
        """
        adjacency: Dict[str, List[str]] = defaultdict(list)
        rel_map: Dict[Tuple[str, str], Relationship] = {}

        # Build adjacency list
        for rel in relationships:
            # Add both directions for undirected traversal
            adjacency[rel.from_memory_id].append(rel.to_memory_id)
            adjacency[rel.to_memory_id].append(rel.from_memory_id)

            # Store relationship in both directions
            rel_map[(rel.from_memory_id, rel.to_memory_id)] = rel

            # For bidirectional relationships, store reverse too
            metadata = self.rel_manager.get_relationship_metadata(rel.type)
            if metadata.bidirectional:
                rel_map[(rel.to_memory_id, rel.from_memory_id)] = rel

        return adjacency, rel_map

    def find_shortest_path(
        self,
        from_memory_id: str,
        to_memory_id: str,
        memories: List[Memory],
        relationships: List[Relationship],
        max_depth: int = 5,
        relationship_types: Optional[List[RelationshipType]] = None
    ) -> Optional[GraphPath]:
        """
        Find the shortest path between two memories using BFS.

        Args:
            from_memory_id: Starting memory ID
            to_memory_id: Target memory ID
            memories: All memory nodes
            relationships: All relationships
            max_depth: Maximum path length to search
            relationship_types: Optional filter for relationship types

        Returns:
            GraphPath if path found, None otherwise
        """
        # Build memory lookup
        memory_map = {m.id: m for m in memories}

        if from_memory_id not in memory_map or to_memory_id not in memory_map:
            return None

        # Build adjacency list
        adjacency, rel_map = self.build_adjacency_lists(memories, relationships)

        # Filter relationships if types specified
        if relationship_types:
            allowed_types = set(relationship_types)
            rel_map = {
                k: v for k, v in rel_map.items()
                if v.type in allowed_types
            }

        # BFS to find shortest path
        queue = deque([(from_memory_id, [from_memory_id], [])])
        visited = {from_memory_id}

        while queue:
            current_id, path_ids, path_rels = queue.popleft()

            # Check depth limit
            if len(path_ids) > max_depth:
                continue

            # Found target
            if current_id == to_memory_id:
                path_memories = [memory_map[mid] for mid in path_ids]
                total_strength = sum(r.properties.strength for r in path_rels)

                return GraphPath(
                    memories=path_memories,
                    relationships=path_rels,
                    total_strength=total_strength,
                    length=len(path_rels)
                )

            # Explore neighbors
            for neighbor_id in adjacency.get(current_id, []):
                # Check if relationship exists (considering filters)
                rel_key = (current_id, neighbor_id)
                if rel_key not in rel_map:
                    continue

                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    new_path = path_ids + [neighbor_id]
                    new_rels = path_rels + [rel_map[rel_key]]
                    queue.append((neighbor_id, new_path, new_rels))

        return None

    def find_all_paths(
        self,
        from_memory_id: str,
        to_memory_id: str,
        memories: List[Memory],
        relationships: List[Relationship],
        max_depth: int = 4,
        max_paths: int = 10
    ) -> List[GraphPath]:
        """
        Find multiple paths between two memories.

        Args:
            from_memory_id: Starting memory ID
            to_memory_id: Target memory ID
            memories: All memory nodes
            relationships: All relationships
            max_depth: Maximum path length
            max_paths: Maximum number of paths to return

        Returns:
            List of GraphPath objects, sorted by strength
        """
        memory_map = {m.id: m for m in memories}

        if from_memory_id not in memory_map or to_memory_id not in memory_map:
            return []

        adjacency, rel_map = self.build_adjacency_lists(memories, relationships)

        paths_found: List[GraphPath] = []

        def dfs(current_id: str, path_ids: List[str], path_rels: List[Relationship],
                visited: Set[str]):
            """DFS helper to find all paths."""
            if len(paths_found) >= max_paths:
                return

            if len(path_ids) > max_depth:
                return

            if current_id == to_memory_id:
                # Found a path
                path_memories = [memory_map[mid] for mid in path_ids]
                total_strength = sum(r.properties.strength for r in path_rels)

                paths_found.append(GraphPath(
                    memories=path_memories,
                    relationships=path_rels,
                    total_strength=total_strength,
                    length=len(path_rels)
                ))
                return

            # Explore neighbors
            for neighbor_id in adjacency.get(current_id, []):
                rel_key = (current_id, neighbor_id)
                if rel_key not in rel_map:
                    continue

                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    dfs(
                        neighbor_id,
                        path_ids + [neighbor_id],
                        path_rels + [rel_map[rel_key]],
                        visited
                    )
                    visited.remove(neighbor_id)

        dfs(from_memory_id, [from_memory_id], [], {from_memory_id})

        # Sort by total strength descending
        paths_found.sort(key=lambda p: p.total_strength, reverse=True)

        return paths_found

    def get_neighbors(
        self,
        memory_id: str,
        memories: List[Memory],
        relationships: List[Relationship],
        depth: int = 1,
        min_strength: float = 0.0,
        relationship_types: Optional[List[RelationshipType]] = None,
        categories: Optional[List[RelationshipCategory]] = None
    ) -> Dict[int, List[Tuple[Memory, Relationship]]]:
        """
        Get neighbors at each depth level.

        Args:
            memory_id: Starting memory ID
            memories: All memory nodes
            relationships: All relationships
            depth: How many hops to traverse
            min_strength: Minimum relationship strength filter
            relationship_types: Optional relationship type filter
            categories: Optional relationship category filter

        Returns:
            Dictionary mapping depth -> list of (memory, relationship) tuples
        """
        memory_map = {m.id: m for m in memories}

        if memory_id not in memory_map:
            return {}

        # Build adjacency
        adjacency, rel_map = self.build_adjacency_lists(memories, relationships)

        # Apply filters
        if relationship_types:
            allowed_types = set(relationship_types)
            rel_map = {
                k: v for k, v in rel_map.items()
                if v.type in allowed_types
            }

        if categories:
            allowed_categories = set(categories)
            rel_map = {
                k: v for k, v in rel_map.items()
                if self.rel_manager.get_relationship_category(v.type) in allowed_categories
            }

        if min_strength > 0:
            rel_map = {
                k: v for k, v in rel_map.items()
                if v.properties.strength >= min_strength
            }

        # BFS to get neighbors at each depth
        neighbors_by_depth: Dict[int, List[Tuple[Memory, Relationship]]] = defaultdict(list)
        visited = {memory_id}
        current_level = [(memory_id, 0, None)]

        while current_level:
            next_level = []

            for current_id, current_depth, incoming_rel in current_level:
                if current_depth >= depth:
                    continue

                for neighbor_id in adjacency.get(current_id, []):
                    rel_key = (current_id, neighbor_id)
                    if rel_key not in rel_map:
                        continue

                    if neighbor_id not in visited:
                        visited.add(neighbor_id)
                        neighbor_mem = memory_map[neighbor_id]
                        neighbor_rel = rel_map[rel_key]

                        neighbors_by_depth[current_depth + 1].append(
                            (neighbor_mem, neighbor_rel)
                        )

                        next_level.append((neighbor_id, current_depth + 1, neighbor_rel))

            current_level = next_level

        return dict(neighbors_by_depth)

    def detect_clusters(
        self,
        memories: List[Memory],
        relationships: List[Relationship],
        min_size: int = 3,
        min_density: float = 0.3
    ) -> List[MemoryCluster]:
        """
        Detect clusters of densely connected memories.

        Uses a simple connected components + density filtering approach.

        Args:
            memories: All memory nodes
            relationships: All relationships
            min_size: Minimum cluster size
            min_density: Minimum cluster density (0.0 to 1.0)

        Returns:
            List of MemoryCluster objects
        """
        memory_map = {m.id: m for m in memories}
        adjacency, rel_map = self.build_adjacency_lists(memories, relationships)

        # Find connected components
        visited = set()
        components: List[Set[str]] = []

        def dfs_component(start_id: str) -> Set[str]:
            """DFS to find connected component."""
            component = set()
            stack = [start_id]

            while stack:
                node_id = stack.pop()
                if node_id in visited:
                    continue

                visited.add(node_id)
                component.add(node_id)

                for neighbor_id in adjacency.get(node_id, []):
                    if neighbor_id not in visited:
                        stack.append(neighbor_id)

            return component

        # Find all components
        for memory_id in memory_map:
            if memory_id not in visited:
                component = dfs_component(memory_id)
                if len(component) >= min_size:
                    components.append(component)

        # Calculate density and create clusters
        clusters = []

        for comp in components:
            # Count internal relationships
            internal_rels = []
            for rel in relationships:
                if rel.from_memory_id in comp and rel.to_memory_id in comp:
                    internal_rels.append(rel)

            # Calculate density
            n = len(comp)
            max_edges = n * (n - 1) / 2  # For undirected graph
            actual_edges = len(internal_rels)
            density = actual_edges / max_edges if max_edges > 0 else 0.0

            # Filter by density
            if density >= min_density:
                # Calculate average strength
                avg_strength = (
                    sum(r.properties.strength for r in internal_rels) / len(internal_rels)
                    if internal_rels else 0.0
                )

                # Collect categories
                categories = set()
                for rel in internal_rels:
                    cat = self.rel_manager.get_relationship_category(rel.type)
                    categories.add(cat)

                # Create cluster
                cluster_memories = [memory_map[mid] for mid in comp]

                clusters.append(MemoryCluster(
                    memories=cluster_memories,
                    internal_relationships=internal_rels,
                    density=density,
                    strength=avg_strength,
                    categories=categories
                ))

        # Sort by size and density
        clusters.sort(key=lambda c: (len(c.memories), c.density), reverse=True)

        return clusters

    def find_bridge_nodes(
        self,
        memories: List[Memory],
        relationships: List[Relationship],
        clusters: Optional[List[MemoryCluster]] = None
    ) -> List[BridgeNode]:
        """
        Identify memories that bridge different clusters.

        Args:
            memories: All memory nodes
            relationships: All relationships
            clusters: Pre-computed clusters (will detect if not provided)

        Returns:
            List of BridgeNode objects
        """
        # Detect clusters if not provided
        if clusters is None:
            clusters = self.detect_clusters(memories, relationships)

        if len(clusters) < 2:
            return []  # Need at least 2 clusters for bridges

        # Build cluster membership map
        memory_to_cluster: Dict[str, int] = {}
        for i, cluster in enumerate(clusters):
            for memory in cluster.memories:
                memory_to_cluster[memory.id] = i

        # Find bridge nodes
        bridge_nodes: List[BridgeNode] = []

        # Check each relationship for cross-cluster connections
        cross_cluster_connections: Dict[str, Set[int]] = defaultdict(set)

        for rel in relationships:
            from_cluster = memory_to_cluster.get(rel.from_memory_id)
            to_cluster = memory_to_cluster.get(rel.to_memory_id)

            # Skip if either node not in a cluster
            if from_cluster is None or to_cluster is None:
                continue

            # Found cross-cluster relationship
            if from_cluster != to_cluster:
                cross_cluster_connections[rel.from_memory_id].add(to_cluster)
                cross_cluster_connections[rel.to_memory_id].add(from_cluster)

        # Create bridge nodes
        memory_map = {m.id: m for m in memories}

        for memory_id, connected_clusters in cross_cluster_connections.items():
            if len(connected_clusters) >= 2:
                # Calculate bridge strength based on number of connections
                # and relationship strengths
                relevant_rels = [
                    r for r in relationships
                    if r.from_memory_id == memory_id or r.to_memory_id == memory_id
                ]

                avg_strength = (
                    sum(r.properties.strength for r in relevant_rels) / len(relevant_rels)
                    if relevant_rels else 0.5
                )

                # Bridge strength: combination of connectivity and relationship strength
                bridge_strength = min(1.0, (len(connected_clusters) / 5.0) * avg_strength)

                bridge_nodes.append(BridgeNode(
                    memory=memory_map[memory_id],
                    connected_clusters=sorted(list(connected_clusters)),
                    bridge_strength=bridge_strength
                ))

        # Sort by bridge strength descending
        bridge_nodes.sort(key=lambda b: b.bridge_strength, reverse=True)

        return bridge_nodes

    def calculate_graph_metrics(
        self,
        memories: List[Memory],
        relationships: List[Relationship]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive graph metrics.

        Args:
            memories: All memory nodes
            relationships: All relationships

        Returns:
            Dictionary with graph metrics:
                - node_count: Total number of memory nodes
                - edge_count: Total number of relationships
                - avg_degree: Average number of connections per node
                - density: Graph density (0.0 to 1.0)
                - avg_strength: Average relationship strength
                - category_distribution: Count of relationships by category
                - type_distribution: Count of relationships by type
        """
        n_nodes = len(memories)
        n_edges = len(relationships)

        if n_nodes == 0:
            return {
                "node_count": 0,
                "edge_count": 0,
                "avg_degree": 0.0,
                "density": 0.0,
                "avg_strength": 0.0,
                "category_distribution": {},
                "type_distribution": {}
            }

        # Calculate degree distribution
        degree_map: Dict[str, int] = defaultdict(int)
        for rel in relationships:
            degree_map[rel.from_memory_id] += 1
            degree_map[rel.to_memory_id] += 1

        avg_degree = sum(degree_map.values()) / n_nodes if n_nodes > 0 else 0.0

        # Calculate density (for undirected graph)
        max_edges = n_nodes * (n_nodes - 1) / 2
        density = n_edges / max_edges if max_edges > 0 else 0.0

        # Calculate average strength
        avg_strength = (
            sum(r.properties.strength for r in relationships) / n_edges
            if n_edges > 0 else 0.0
        )

        # Category distribution
        category_dist: Dict[str, int] = defaultdict(int)
        for rel in relationships:
            cat = self.rel_manager.get_relationship_category(rel.type)
            category_dist[cat.value] += 1

        # Type distribution
        type_dist: Dict[str, int] = defaultdict(int)
        for rel in relationships:
            type_dist[rel.type.value] += 1

        return {
            "node_count": n_nodes,
            "edge_count": n_edges,
            "avg_degree": avg_degree,
            "density": density,
            "avg_strength": avg_strength,
            "category_distribution": dict(category_dist),
            "type_distribution": dict(type_dist)
        }


# Singleton instance for easy access
graph_analyzer = GraphAnalyzer()
