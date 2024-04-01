"""The new version of graphs."""
from __future__ import annotations
from typing import Optional, Any, TextIO
from collections import deque
from queue_utils import PriorityQueue
import folium


class _Vertex:
    """A vertex representing a junction"""
    junc_id: int
    upstream: set[_Vertex]
    downstream: set[_Vertex]
    coordinates: list[int | float]
    message: str

    def __init__(self, junc_id: int, coord: list[int | float], message: str = '') -> None:
        self.junc_id = junc_id
        self.coordinates = coord
        self.upstream = set()
        self.downstream = set()
        self.message = message

    def get_coordinates(self) -> list[int | float]:
        """Return the coordinates of the junction."""
        return self.coordinates.copy()

    def add_message(self, message: str) -> None:
        """Add a message that appears in the popup of the marker of this vertex."""
        self.message = message

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

    def __init__(self, start_id: int, end_id: int, ogf_ids: set[int], length: float,
                 segments: Optional[set[_Segment]] = None) -> None:
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
            total_time += segment.seg_length / (segment.speed_limit * 1e3)
        self.info['travel_time'] = total_time

    def add_segment(self, segment: _Segment) -> None:
        """Add a segment to this edge."""
        if segment.corr_ogfid in self.ogf_ids:
            self.segments.add(segment)

    def get_polylines(self) -> set[folium.PolyLine]:
        """Return a set of polylines of the segments in this edge."""
        return {folium.PolyLine(locations=segment.coordinates,
                                popup=f"name: {segment.name};\n"
                                      f"length: {round(segment.seg_length / 1e3, 3)}km;\n"
                                      f"road class: {segment.road_class};\n"
                                      f"speed limit: {segment.speed_limit}km/h") for segment in self.segments}

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
    seg_length: float
    road_class: str
    speed_limit: int
    coordinates: list[list[float]]

    def __init__(self, ogfid: int, length: float, road_class: str, speed_limit: int,
                 coordinates: list[list[int | float]], name: str = '') -> None:
        self.corr_ogfid = ogfid
        self.name = name
        self.seg_length = length
        self.road_class = road_class
        self.speed_limit = speed_limit
        self.coordinates = coordinates


class Graph:
    """The graph representing a road network."""
    _vertices: dict[int, _Vertex]
    _edges: dict[tuple[int, int], _Edge]

    def __init__(self) -> None:
        self._vertices = {}
        self._edges = {}

    def __contains__(self, item: int | tuple[int, int]) -> bool:
        if isinstance(item, int):
            return item in self._vertices
        elif isinstance(item, tuple):
            return item in self._edges
        else:
            raise ValueError

    def add_vertex(self, junc_id: int, coord: list[int | float], message: str = '') -> None:
        """Add a vertex to the graph. Do nothing if it already exists."""
        if junc_id not in self._vertices:
            self._vertices[junc_id] = _Vertex(junc_id, coord, message)

    def get_vertex_coordinates(self, junc_id: int) -> list[int | float]:
        """Get the coordinates of the vertex with junc_id.
        Raise ValueError if junc_id is not in self._vertices.
        """
        if junc_id in self._vertices:
            return self._vertices[junc_id].coordinates
        else:
            raise ValueError

    def add_edge_with_segments(self, start_id: int, end_id: int, ogf_ids: set[int],
                               length: float, weight_type: str, segments_info: list[tuple]) -> None:
        """Add an edge containing segments with properties given by segments_info into the graph.
        If an edge already exists from start_id to end_id, replace it if the new edge has a lower weight of type
        weight_type and do nothing otherwise.
        Raise ValueError if start_id not in self._vertices or end_id not in self._vertices.

        Preconditions:
            - all(seg_info[0] in ogf_ids for seg_info in segments_info)
            - weight_type in {"distance", "travel_time"}
        """
        if start_id in self._vertices and end_id in self._vertices:
            segments = set()
            for ogf_id, seg_len, rc, speed_lim, coordinates, road_name in segments_info:
                segments.add(_Segment(ogf_id, seg_len, rc, speed_lim,
                                      coordinates, road_name))
            new_edge = _Edge(start_id, end_id, ogf_ids, length, segments)
            if (start_id, end_id) not in self._edges:
                u = self._vertices[start_id]
                v = self._vertices[end_id]
                u.downstream.add(v)
                v.upstream.add(u)
                self._edges[(start_id, end_id)] = new_edge
            elif self._edges[(start_id, end_id)].info[weight_type] > new_edge.info[weight_type]:
                self._edges[(start_id, end_id)] = new_edge
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

    def get_weight(self, start_id: int, end_id: int, weight_type: str) -> float:
        """Return the weight of the edge from self._vertices[start_id] to self._vertices[end_id].
        Raise ValueError if (start_id, end_id) is not in self._edges.
        """
        if (start_id, end_id) in self._edges:
            return self._edges[(start_id, end_id)].info[weight_type]
        else:
            raise ValueError

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

    def prune_graph(self, protected_ids: set[int], pruned_classes: set[str]) -> None:
        """Improved version of pruning the graph."""
        preserved_equiv_classes = self.get_preserved_equiv_classes(protected_ids, pruned_classes)
        potentially_pruned_equiv_classes = self.get_pruned_equiv_classes(pruned_classes)
        to_prune = set()
        for pruned_equiv_class in potentially_pruned_equiv_classes:
            count = 0
            for preserved_equiv_class in preserved_equiv_classes:
                if not pruned_equiv_class.isdisjoint(preserved_equiv_class):
                    count += 1
            if count <= 1:
                to_prune.update(pruned_equiv_class)
        edges = self._edges.copy()
        for start_id, end_id in edges:
            if start_id in to_prune and end_id in to_prune and (start_id, end_id) in self._edges and \
                    self._edges[(start_id, end_id)].all_in_road_classes(pruned_classes):
                self.remove_edge(start_id, end_id)

    def get_preserved_equiv_classes(self, protected_ids: set[int], pruned_classes: set[str]) -> list[set[int]]:
        """Return a list of sets of vertex ids satisfying the following properties:
            - For every 2 sets in the returned list, they are disjoint.
            - For every ordered pair (u, v) of vertices such that u.junc_id and v.junc_id are in the same set
            in the returned list, it is possible to travel from u to v AND from v to u using a path that do not use
            any road belonging to a class in pruned_classes.
            - For every id in protected_ids, id is in a set in the returned list.
        """
        visited = set()
        res = []
        for k in self._vertices:
            if k not in visited:
                vertex = self._vertices[k]
                to_check_downstream = deque([u.junc_id for u in vertex.downstream if
                                             not self._edges[(k, u.junc_id)].all_in_road_classes(pruned_classes)])
                to_check_upstream = deque([v.junc_id for v in vertex.upstream if
                                           not self._edges[(v.junc_id, k)].all_in_road_classes(pruned_classes)])
                if k in protected_ids or (len(to_check_upstream) > 0 and len(to_check_downstream) > 0):
                    downstream_connected = {k}.union(set(to_check_downstream))
                    upstream_connected = {k}.union(set(to_check_upstream))
                    while len(to_check_downstream) > 0:
                        u = self._vertices[to_check_downstream.popleft()]
                        for v in u.downstream:
                            if v.junc_id not in downstream_connected and \
                                    not self._edges[(u.junc_id, v.junc_id)].all_in_road_classes(pruned_classes):
                                downstream_connected.add(v.junc_id)
                                to_check_downstream.append(v.junc_id)
                    while len(to_check_upstream) > 0:
                        u = self._vertices[to_check_upstream.popleft()]
                        for v in u.upstream:
                            if v.junc_id not in upstream_connected and \
                                    not self._edges[(v.junc_id, u.junc_id)].all_in_road_classes(pruned_classes):
                                upstream_connected.add(v.junc_id)
                                to_check_upstream.append(v.junc_id)
                    equivalence_class = downstream_connected.intersection(upstream_connected)
                    visited.update(equivalence_class)
                    res.append(equivalence_class)
        return res

    def get_pruned_equiv_classes(self, pruned_classes: set[str]) -> list[set[int]]:
        """Return a list of sets of vertex ids satisfying the following properties:
            - For any 2 sets in the returned list, they are disjoint.
            - For any pair of ordered pair of vertices (u, v) such that u.junc_id and v.junc_id are in the same
            set in the returned list, they are connected by roads belonging to pruned classes in an undirected sense.
            (i.e. It would be possible to travel from u to v AND from v to u along a route that only
            uses roads belonging to pruned classes if every road in the network permits traffic in both directions.)
        """
        visited = set()
        res = []
        for k in self._vertices:
            if k not in visited:
                vertex = self._vertices[k]
                adjacent = vertex.upstream.union(vertex.downstream)
                to_check = deque([u.junc_id for u in adjacent if
                                  ((k, u.junc_id) in self._edges and
                                   self._edges[(k, u.junc_id)].all_in_road_classes(pruned_classes)) or
                                  ((u.junc_id, k) in self._edges and
                                   self._edges[(u.junc_id, k)].all_in_road_classes(pruned_classes))])
                if len(to_check) > 0:
                    equivalence_class = {k}.union(set(to_check))
                    while len(to_check) > 0:
                        u = self._vertices[to_check.popleft()]
                        cur_adjacent = u.upstream.union(u.downstream)
                        for v in cur_adjacent:
                            if v.junc_id not in equivalence_class:
                                if ((u.junc_id, v.junc_id) in self._edges and
                                    self._edges[(u.junc_id, v.junc_id)].all_in_road_classes(pruned_classes)) or \
                                        ((v.junc_id, u.junc_id) in self._edges and
                                         self._edges[(v.junc_id, u.junc_id)].all_in_road_classes(pruned_classes)):
                                    equivalence_class.add(v.junc_id)
                                    to_check.append(v.junc_id)
                    visited.update(equivalence_class)
                    res.append(equivalence_class)
        return res

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
            vertex = self._vertices[junc_id]
            m.add_child(folium.Marker(location=vertex.coordinates, popup=f"id: {junc_id}\n" + vertex.message))
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
        m.add_child(folium.Marker(location=self._vertices[route[0]].coordinates,
                                  popup=f"id: {self._vertices[route[0]].junc_id}\n" + self._vertices[route[0]].message))
        m.add_child(folium.Marker(location=self._vertices[route[-1]].coordinates,
                                  popup=f"id: {self._vertices[route[-1]].junc_id}\n" +
                                        self._vertices[route[-1]].message))
        m.save(file_path)
        return m

    def write_graph(self, output_file: TextIO, weight_type: str,
                    vertices_of_interest: list[int], pruned_classes: set[str]) -> None:
        """Write the graph to a txt file.

        Preconditions:
            - all(_id in self._vertices for _id in vertices_of_interest)
        """
        output_file.write(weight_type + "\n")
        output_file.write(" ".join([str(junc_id) for junc_id in vertices_of_interest]) + "\n")
        output_file.write("|".join(list(pruned_classes)) + "\n")
        output_file.write(f"V {len(self._vertices)}\n")
        for junc_id in self._vertices:
            output_file.write(str(junc_id) + "\n")
            output_file.write(" ".join([str(c) for c in self._vertices[junc_id].coordinates]) + "\n")
        output_file.write(f"E {len(self._edges)}\n")
        for start_id, end_id in self._edges:
            edge = self._edges[(start_id, end_id)]
            output_file.write(f"e {start_id} {end_id}\n")
            output_file.write(" ".join([str(ogfid) for ogfid in edge.ogf_ids]) + "\n")
            output_file.write(f"d {edge.info["distance"]}\n")
            output_file.write(f"t {edge.info["travel_time"]}\n")
            for segment in edge.segments:
                output_file.write(f"S {segment.corr_ogfid}\n")
                output_file.write(str(segment.seg_length) + "\n")
                output_file.write(segment.road_class + "\n")
                output_file.write(str(segment.speed_limit) + "\n")
                locs = [f"{c[0]},{c[1]}" for c in segment.coordinates]
                output_file.write(" ".join(locs) + "\n")
                output_file.write(segment.name + "\n")
        output_file.write("END")
