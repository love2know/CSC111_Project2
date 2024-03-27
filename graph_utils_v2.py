"""The new version of graphs."""
from __future__ import annotations
from typing import Optional, Any
import folium


class _Vertex:
    """A vertex representing a junction"""
    junc_id: int
    neighbours: set[_Vertex]
    marker: folium.Marker

    def __init__(self, junc_id: int, marker: folium.Marker, neighbours: Optional[set[_Vertex]] = None) -> None:
        self.junc_id = junc_id
        self.marker = marker
        if neighbours is not None:
            self.neighbours = neighbours
        else:
            self.neighbours = set()


class _Edge:
    """An edge representing a road.

    Representation Invariants:
        - 'distance' in self.info
        - 'travel_time' in self.info
    """
    start_id: int
    end_id: int
    segments: set[_Segment]
    info: dict[str, Any]

    def __init__(self, start_id: int, end_id: int, length: float, segments: Optional[set[_Segment]] = None) -> None:
        self.start_id = start_id
        self.end_id = end_id
        self.info = {'distance': length, 'travel_time': 0.0}
        if segments is not None:
            self.segments = segments
            self.update_travel_time()
        else:
            self.segments = set()

    def update_travel_time(self) -> None:
        """Update the travel time for traversing this edge.
        """
        total_time = 0.0
        for segment in self.segments:
            total_time += segment.length / (segment.speed_limit * 1e3)
        self.info['travel_time'] = total_time


class _Segment:
    """A segment in a road.

    Representation Invariants:
        - self.length > 0
    """
    corr_ogfid: int
    name: str
    length: float
    road_class: str
    speed_limit: float
    poly_line: folium.PolyLine

    def __init__(self, ogfid: int, length: float, road_class: str, speed_limit: float, poly_line: folium.PolyLine,
                 name: str = '') -> None:
        self.corr_ogfid = ogfid
        self.name = name
        self.length = length
        self.road_class = road_class
        self.speed_limit = speed_limit
        self.poly_line = poly_line


class Graph:
    """The graph representing a road network."""
    _vertices: dict[int, _Vertex]
    _edges: dict[tuple[int, int], _Edge]

    def __init__(self) -> None:
        self._vertices = {}
        self._edges = {}

    def add_vertex(self, junc_id: int, coords: list[float], message: str = '') -> None:
        """Add a vertex to the graph. Do nothing if it already exists."""
        if junc_id not in self._vertices:
            marker = folium.Marker(location=coords, popup=f'id: {junc_id}\n' + message)
            self._vertices[junc_id] = _Vertex(junc_id, marker)

    def add_edge(self, start_id: int, end_id: int, length: float) -> None:
        """Add an edge to the graph. If the edge already exists, replace it if the new edge
        is shorter and do nothing otherwise.
        Raise ValueError if start_id not in self._vertices or end_id not in self._vertices.
        """
        if start_id in self._vertices and end_id in self._vertices:
            if (start_id, end_id) not in self._edges:
                u = self._vertices[start_id]
                v = self._vertices[end_id]
                u.neighbours.add(v)
                self._edges[(start_id, end_id)] = _Edge(start_id, end_id, length)
            elif self._edges[(start_id, end_id)].info['distance'] > length:
                self._edges[(start_id, end_id)] = _Edge(start_id, end_id, length)
        else:
            raise ValueError

    def add_segment_to_edge(self, start_id: int, end_id: int,
                            corr_ogfid: int, length: float,
                            road_class: str, speed_limit: float,
                            coords: list[list[float]], name: str = '',
                            message: str = '') -> None:
        """Add a segment to the edge from start_id to end_id.
        Raise ValueError if start_id not in self._vertices or end_id not in self._vertices
        """
        if start_id in self._vertices and end_id in self._vertices:
            poly_line = folium.PolyLine(locations=coords,
                                        popup=f'road name: {name} \n road class: {road_class} \n'
                                              f'length: {length} \n speed limit: {speed_limit} \n'
                                              f'{message}')
            segment = _Segment(corr_ogfid, length, road_class,
                               speed_limit, poly_line, name)
            self._edges[(start_id, end_id)].segments.add(segment)
        else:
            raise ValueError
