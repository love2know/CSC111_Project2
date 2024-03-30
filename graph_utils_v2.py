"""The new version of graphs."""
from __future__ import annotations
from typing import Optional, Any
from collections import deque
from queue_utils import PriorityQueue
import folium


class _Vertex:
    """A vertex representing a junction"""
    junc_id: int
    upstream: set[_Vertex]
    downstream: set[_Vertex]
    marker: folium.Marker

    def __init__(self, junc_id: int, marker: folium.Marker) -> None:
        self.junc_id = junc_id
        self.marker = marker
        self.upstream = set()
        self.downstream = set()

    def add_message(self, message: str) -> None:
        """Add a message that appears in the popup of the marker of this vertex."""
        self.marker.add_child(folium.Popup(f"id: {self.junc_id}\n" + message))

    def in_degree(self) -> int:
        """Return the in-degree of this vertex."""
        return len(self.upstream)

    def out_degree(self) -> int:
        """Return the out-degree of this vertex."""
        return len(self.downstream)

class _Edge:
    """An edge representing a road.

    Representation Invariants:
        - 'distance' in self.info
        - 'travel_time' in self.info
    """
    start_id: int
    end_id: int
    ogf_ids: set[int]
    segments: set[_Segment]
    info: dict[str, Any]

    def __init__(self, start_id: int, end_id: int, ogf_ids: set[int], length: float, segments: Optional[set[_Segment]] = None) -> None:
        self.start_id = start_id
        self.end_id = end_id
        self.ogf_ids = ogf_ids
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

    def add_segment(self, segment: _Segment) -> None:
        """Add a segment to this edge."""
        if segment.corr_ogfid in self.ogf_ids:
            self.segments.add(segment)

    def get_polylines(self) -> set[folium.PolyLine]:
        """Return a set of polylines of the segments in this edge."""
        return {segment.poly_line for segment in self.segments}

    def all_in_road_classes(self, road_classes: set[str]) -> bool:
        """Determine if all segments in the edge belongs to one road class in road_classes.
        """
        return all(segment.road_class in road_classes for segment in self.segments)

    def any_in_road_classes(self, road_classes: set[str]) -> bool:
        """Determine if any segments in the edge belongs to one road class in road_classes.
        """
        return any(segment.road_class in road_classes for segment in self.segments)


class _Segment:
    """A segment in a road.

    Representation Invariants:
        - self.length > 0
    """
    corr_ogfid: int
    name: str
    length: float
    road_class: str
    speed_limit: int
    poly_line: folium.PolyLine

    def __init__(self, ogfid: int, length: float, road_class: str, speed_limit: int, poly_line: folium.PolyLine,
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

    def add_vertex(self, junc_id: int, coord: list[float], message: str = '') -> None:
        """Add a vertex to the graph. Do nothing if it already exists."""
        if junc_id not in self._vertices:
            marker = folium.Marker(location=coord, popup=f'id: {junc_id}\n' + message)
            self._vertices[junc_id] = _Vertex(junc_id, marker)

    def add_edge(self, start_id: int, end_id: int, ogf_ids: set[int], length: float) -> None:
        """Add an edge to the graph. If the edge already exists, replace it if the new edge
        is shorter and do nothing otherwise.
        Raise ValueError if start_id not in self._vertices or end_id not in self._vertices.
        """
        if start_id in self._vertices and end_id in self._vertices:
            if (start_id, end_id) not in self._edges:
                u = self._vertices[start_id]
                v = self._vertices[end_id]
                u.downstream.add(v)
                v.upstream.add(u)
                self._edges[(start_id, end_id)] = _Edge(start_id, end_id, ogf_ids, length)
            elif self._edges[(start_id, end_id)].info['distance'] > length:
                self._edges[(start_id, end_id)] = _Edge(start_id, end_id, ogf_ids, length)
        else:
            raise ValueError

    def add_segment_to_edge(self, start_id: int, end_id: int,
                            corr_ogfid: int, length: float,
                            road_class: str, speed_limit: int,
                            coords: list[list[float]], name: str = '',
                            message: str = '') -> None:
        """Add a segment to the edge from start_id to end_id.
        Raise ValueError if start_id not in self._vertices or end_id not in self._vertices.
        """
        if start_id in self._vertices and end_id in self._vertices:
            edge = self._edges[(start_id, end_id)]
            if corr_ogfid in edge.ogf_ids:
                poly_line = folium.PolyLine(locations=coords,
                                            popup=f'road name: {name} \n road class: {road_class} \n'
                                                  f'length: {length} \n speed limit: {speed_limit} \n'
                                                  f'{message}')
                segment = _Segment(corr_ogfid, length, road_class,
                                   speed_limit, poly_line, name)
                edge.add_segment(segment)
        else:
            raise ValueError

    def add_message_to_vertices(self, messages: dict[int, str]) -> None:
        """Add messages to certain vertices"""
        for junc_id in messages:
            self._vertices[junc_id].add_message(messages[junc_id])

    def vertex_count(self) -> int:
        """Return the number of vertices in the graph."""
        return len(self._vertices)

    def edge_count(self) -> int:
        """Return the number of edges in the graph."""
        return len(self._edges)

    def remove_edge(self, start_id: int, end_id: int) -> None:
        """Removes an edge from start_id to end_id.
        Do nothing if (start_id, end_id) not in self._edges.
        """
        if (start_id, end_id) in self._edges:
            u = self._vertices[start_id]
            v = self._vertices[end_id]
            u.downstream.remove(v)
            v.upstream.remove(u)
            self._edges.pop((start_id, end_id))

    def prune_graph(self, protected_ids: list[int], pruned_classes: set[str]) -> None:
        """Prune the graph by removing all edges belonging to pruned_classes while protecting
        the vertices with ids in protected_ids. The removal should leave a cluster surrounding
        each protected vertex intact.

        Preconditions:
            - all(pid in self._vertices for pid in protected_ids)
        """
        protected_cluster = set()
        for protected_id in protected_ids:
            protected_cluster.update(self.get_protected_cluster(protected_id, pruned_classes))
        edges = self._edges.copy()
        for e in edges:
            start_id, end_id = e
            if e in self._edges and start_id not in protected_cluster and end_id not in protected_cluster \
                    and self._edges[e].all_in_road_classes(pruned_classes):
                self.remove_edge(start_id, end_id)

    def get_protected_cluster(self, protected_id: int, pruned_classes: set[str]) -> set[int]:
        """Get the area protected from pruning to ensure that the vertex
        with protected_id can be connected to the rest of the network.
        Raise ValueError if protected_id not in self._vertices.
        """
        if protected_id in self._vertices:
            downstream_protection = set()
            upstream_protection = set()
            to_check_downstream = deque()
            to_check_upstream = deque()
            to_check_downstream.append(protected_id)
            to_check_upstream.append(protected_id)
            while len(to_check_downstream) > 0:
                curr_id = to_check_downstream.popleft()
                v = self._vertices[curr_id]
                downstream_protection.add(curr_id)
                if all(self._edges[(curr_id, u.junc_id)].all_in_road_classes(pruned_classes) for u in v.downstream):
                    for u in v.downstream:
                        if u.junc_id not in downstream_protection:
                            to_check_downstream.append(u.junc_id)
            while len(to_check_upstream) > 0:
                curr_id = to_check_upstream.popleft()
                v = self._vertices[curr_id]
                upstream_protection.add(curr_id)
                if all(self._edges[(u.junc_id, curr_id)].all_in_road_classes(pruned_classes) for u in v.upstream):
                    for u in v.upstream:
                        if u.junc_id not in upstream_protection:
                            to_check_upstream.append(u.junc_id)
            return upstream_protection.union(downstream_protection)
        else:
            raise ValueError

    def remove_redundant_vertices(self, weight_type: str, protected_ids: set[int]) -> None:
        """After pruning, since certain roads are removed, there will be some vertices
        that simply acts as a point on a non-branching road. It's desirable to remove a vertex
        of this kind and connect the 2 edges separated by the vertex into a single continuous edge.

        Preconditions:
            - weight_type in {'distance', 'travel_time'}
        """
        vertices = set(self._vertices.values())
        for vertex in vertices:
            if vertex.junc_id in self._vertices and vertex.junc_id not in protected_ids:
                if vertex.in_degree() == 0 and vertex.out_degree() == 0:
                    self._vertices.pop(vertex.junc_id)
                elif vertex.in_degree() == 1 and vertex.out_degree() == 1 and vertex.upstream != vertex.downstream:
                    self._vertices.pop(vertex.junc_id)
                    v1 = vertex.upstream.pop()
                    v2 = vertex.downstream.pop()
                    v1.downstream.remove(vertex)
                    v2.upstream.remove(vertex)
                    in_edge = self._edges[(v1.junc_id, vertex.junc_id)]
                    out_edge = self._edges[(vertex.junc_id, v2.junc_id)]
                    if (v1.junc_id, v2.junc_id) not in self._edges or \
                            self._edges[(v1.junc_id, v2.junc_id)].info[weight_type] > \
                            in_edge.info[weight_type] + out_edge.info[weight_type]:
                        new_edge = _Edge(v1.junc_id, v2.junc_id, in_edge.ogf_ids.union(out_edge.ogf_ids),
                                         in_edge.info['distance'] + out_edge.info['distance'],
                                         in_edge.segments.union(out_edge.segments))
                        self._edges[(v1.junc_id, v2.junc_id)] = new_edge
                    v1.downstream.add(v2)
                    v2.upstream.add(v1)
                    self._edges.pop((v1.junc_id, vertex.junc_id))
                    self._edges.pop((vertex.junc_id, v2.junc_id))
                elif vertex.in_degree() == 2 and vertex.out_degree() == 2 and vertex.upstream == vertex.downstream:
                    self._vertices.pop(vertex.junc_id)
                    v1 = vertex.downstream.pop()
                    v2 = vertex.downstream.pop()
                    vertex.upstream.clear()
                    v1.downstream.remove(vertex)
                    v1.upstream.remove(vertex)
                    v2.downstream.remove(vertex)
                    v2.upstream.remove(vertex)
                    e1 = self._edges[(v1.junc_id, vertex.junc_id)]
                    e2 = self._edges[(vertex.junc_id, v2.junc_id)]
                    e3 = self._edges[(v2.junc_id, vertex.junc_id)]
                    e4 = self._edges[(vertex.junc_id, v1.junc_id)]
                    if (v1.junc_id, v2.junc_id) not in self._edges or \
                            self._edges[(v1.junc_id, v2.junc_id)].info[weight_type] > \
                            e1.info[weight_type] + e2.info[weight_type]:
                        new_edge1 = _Edge(v1.junc_id, v2.junc_id, e1.ogf_ids.union(e2.ogf_ids),
                                          e1.info['distance'] + e2.info['distance'],
                                          e1.segments.union(e2.segments))
                        self._edges[(v1.junc_id, v2.junc_id)] = new_edge1
                    v1.downstream.add(v2)
                    v2.upstream.add(v1)
                    self._edges.pop((v1.junc_id, vertex.junc_id))
                    self._edges.pop((vertex.junc_id, v2.junc_id))
                    if (v2.junc_id, v1.junc_id) not in self._edges or \
                            self._edges[(v2.junc_id, v1.junc_id)].info[weight_type] > \
                            e3.info[weight_type] + e4.info[weight_type]:
                        new_edge2 = _Edge(v2.junc_id, v1.junc_id, e3.ogf_ids.union(e4.ogf_ids),
                                          e3.info['distance'] + e4.info['distance'],
                                          e3.segments.union(e4.segments))
                        self._edges[(v2.junc_id, v1.junc_id)] = new_edge2
                    v2.downstream.add(v1)
                    v1.upstream.add(v2)
                    self._edges.pop((v2.junc_id, vertex.junc_id))
                    self._edges.pop((vertex.junc_id, v1.junc_id))

    def update_travel_times(self) -> None:
        """Update the travel time of all edges in the graph.
        """
        for e in self._edges:
            self._edges[e].update_travel_time()

    def find_shortest_path(self, start_id: int, end_id: int, weight_type: str) -> Optional[tuple[list[int], float]]:
        """Find the shortest path from start_id to end_id using Dijkstra's algorithm.
        Raise ValueError if start_id or end_id are not in self._vertices.
        Preconditions:
            - weight_type in {'distance', 'travel_time'}
        """
        if start_id not in self._vertices or end_id not in self._vertices:
            raise ValueError
        elif start_id == end_id:
            return [start_id], 0.0
        else:
            dist = {start_id: 0.0}
            prev = {start_id: None}
            q = PriorityQueue()
            visited = set()
            q.enqueue(self._vertices[start_id], 0.0)
            while not q.is_empty():
                u = q.dequeue()
                visited.add(u)
                if u.junc_id == end_id:
                    break
                for v in u.downstream:
                    if v not in visited:
                        cur_edge = self._edges[(u.junc_id, v.junc_id)]
                        cur_dist = dist[u.junc_id] + cur_edge.info[weight_type]
                        if v.junc_id not in dist or dist[v.junc_id] > cur_dist:
                            dist[v.junc_id] = cur_dist
                            prev[v.junc_id] = u.junc_id
                            if v not in q:
                                q.enqueue(v, cur_dist)
                            else:
                                q.update_priority(v, cur_dist)
            if end_id not in dist:
                return None
            else:
                path = []
                cur_id = end_id
                while cur_id is not None:
                    path.append(cur_id)
                    cur_id = prev[cur_id]
                path.reverse()
                return path, dist[end_id]

    def visualize_vertices(self, selected_vertices: set[int], file_path: str) -> folium.Map:
        """Save a map in which selected vertices are shown as markers."""
        m = folium.Map(location=[43.07880556, -79.07886111])  # The coordinates of Niagara Fall.
        for junc_id in selected_vertices:
            m.add_child(self._vertices[junc_id].marker)
        m.save(file_path)
        return m

    def visualize_route(self, route: list[int], file_path: str, existing_map: Optional[folium.Map] = None) -> \
            folium.Map:
        """Save a map in which the planned route is shown as polylines."""
        if existing_map is not None:
            m = existing_map
        else:
            m = folium.Map(location=[43.07880556, -79.07886111])
        for i in range(len(route) - 1):
            edge = self._edges[(route[i], route[i + 1])]
            polylines = edge.get_polylines()
            for polyline in polylines:
                m.add_child(polyline)
        m.add_child(self._vertices[route[0]].marker)
        m.add_child(self._vertices[route[-1]].marker)
        m.save(file_path)
        return m
