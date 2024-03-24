"""A module containing the Graph class."""
from __future__ import annotations
from typing import Optional
import folium


class _RoadVertex:
    """A class representing a vertex in the graph."""
    id: int
    marker: folium.Marker
    neighbours: dict[_RoadVertex, float]

    def __init__(self, junction_id: int, marker: folium.Marker, neighbours: Optional[dict[_RoadVertex, float]] = None) \
            -> None:
        self.id = junction_id
        self.marker = marker
        if neighbours is not None:
            self.neighbours = neighbours
        else:
            self.neighbours = {}


class RoadGraph:
    """A class representing the road network.
    Each vertex represents a junction and each edge represents a road from a junction to another junction.
    The graph is DIRECTED!!!!!!
    """
    _vertices: dict[int, _RoadVertex]
    _segments_of_edges: dict[tuple[_RoadVertex, _RoadVertex], set[folium.PolyLine]]

    def __init__(self) -> None:
        self._vertices = {}
        self._segments_of_edges = {}

    def __contains__(self, item) -> bool:
        return item in self._vertices

    def vertex_count(self) -> int:
        """Returns the number of vertices in the graph"""
        return len(self._vertices)

    def edge_count(self) -> int:
        """Returns the number of DIRECTED edges in the graph"""
        return len(self._segments_of_edges)

    def get_vertex(self, junction_id: int) -> _RoadVertex:
        """Get a vertex by its junction id."""
        return self._vertices[junction_id]

    def add_vertex(self, junction_id: int, marker: folium.Marker) -> None:
        """Add a vertex representing the junction with junction_id to the graph.
        If it's already present, do nothing.
        """
        if junction_id not in self._vertices:
            self._vertices[junction_id] = _RoadVertex(junction_id, marker)

    def add_edge(self, start: int, end: int, weight: float) -> None:
        """Add an edge FROM the vertex with id start TO the vertex with id end
        with weight.
        Otherwise, do nothing.
        """
        if start not in self._vertices or end not in self._vertices:
            raise ValueError("The desired junctions are not present.")
        u = self._vertices[start]
        v = self._vertices[end]
        if v not in u.neighbours:
            u.neighbours[v] = weight
            self._segments_of_edges[(u, v)] = set()

    def get_weight(self, start_id: int, end_id: int) -> float:
        """Return the weight of the edge FROM the vertex with id start_id TO the vertex with id end_id.
        Raise ValueError if start or end are not present in self._vertices or if end is not a neighbor of start.
        """
        if start_id not in self._vertices or end_id not in self:
            raise ValueError("The desired junctions are not present.")
        else:
            u = self._vertices[start_id]
            v = self._vertices[end_id]
            if v in u.neighbours:
                return u.neighbours[v]
            else:
                raise ValueError("There is no edge from the start vertex to the end vertex.")

    def update_weight(self, start: int, end: int, new_weight: float) -> None:
        """Modify the weight of the edge FROM the vertex with id start TO the vertex with id end.

        Raise ValueError if start or end are not present in the graph or if end is not a neighbour of start.
        """
        if start not in self._vertices or end not in self._vertices:
            raise ValueError("The desired junctions are not present.")
        else:
            u = self._vertices[start]
            v = self._vertices[end]
            if v in u.neighbours:
                u.neighbours[v] = new_weight
            else:
                raise ValueError("There's no edge from the start vertex to the end vertex.")

    def add_segment_to_edge(self, start: int, end: int, segment: folium.PolyLine) -> None:
        """Add a segment to the edge FROM the vertex with the id start TO the vertex with id end
        Raise ValueError if start or end are not present in the graph or if end is not a neighbour of start.
        """
        if start not in self._vertices or end not in self._vertices:
            raise ValueError("The desired junctions are not present.")
        else:
            u = self._vertices[start]
            v = self._vertices[end]
            if v in u.neighbours:
                self._segments_of_edges[(u, v)].add(segment)
            else:
                raise ValueError("There's no edge from the start vertex to the end vertex.")

    def to_map(self) -> folium.Map:
        """Visualize the road network with a leaflet.js map!!!!!!!!!!"""
        m = folium.Map(location=[43.0, -79.0], zoom_control=True)
        i = 0
        j = 0
        for junc_id in self._vertices:
            u = self._vertices[junc_id]
            u.marker.add_to(m)
            i += 1
            print(i)
        for edge in self._segments_of_edges:
            for pl in self._segments_of_edges[edge]:
                pl.add_to(m)
                j += 1
                print(j)
        return m
