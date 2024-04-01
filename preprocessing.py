"""Improved version of preprocessing."""
from typing import Optional, TextIO
import json
import math
import folium
from graph_utils import Graph


def data_to_graph(road_elem_data: TextIO, segment_data: TextIO,
                  weight_type: str, vertices_of_interest: dict[int, str]) -> Graph:
    """Load data and create graph.

    Preconditions:
        - weight_type in {distance, travel_time}
    """
    road_elements = json.load(road_elem_data)
    road_segments = json.load(segment_data)
    graph = Graph()
    id_to_segment_info = {}
    for segment in road_segments["features"]:
        road_segment_type = segment["properties"]["ROAD_ELEMENT_TYPE"]
        speed_limit = segment["properties"]["SPEED_LIMIT"]
        if road_segment_type != "VIRTUAL ROAD" and (road_segment_type == "FERRY CONNECTION" or speed_limit is not None):
            if speed_limit is None:
                speed_limit = 34
            ogfid = segment["properties"]["ROAD_NET_ELEMENT_ID"]
            name = segment["properties"]["FULL_STREET_NAME"]
            if name is None:
                name = ''
            length = segment["properties"]["LENGTH"]
            road_class = segment["properties"]["ROAD_CLASS"]
            coords = segment["geometry"]["coordinates"]
            if all(len(c) == 2 and isinstance(c[0], int | float) and isinstance(c[1], int | float) for c in coords):
                for c in coords:
                    c.reverse()
                if ogfid not in id_to_segment_info:
                    id_to_segment_info[ogfid] = [(ogfid, length, road_class, speed_limit, coords, name)]
                else:
                    id_to_segment_info[ogfid].append((ogfid, length, road_class, speed_limit, coords, name))
    for road_elem in road_elements["features"]:
        ogfid = road_elem["properties"]["OGF_ID"]
        from_id = road_elem["properties"]["FROM_JUNCTION_ID"]
        to_id = road_elem["properties"]["TO_JUNCTION_ID"]
        from_coord = road_elem["geometry"]["coordinates"][0]
        to_coord = road_elem["geometry"]["coordinates"][-1]
        if ogfid in id_to_segment_info and from_id != to_id \
                and all(isinstance(c, int | float) for c in from_coord) and \
                all(isinstance(c, int | float) for c in to_coord):
            from_coord.reverse()
            to_coord.reverse()
            graph.add_vertex(from_id, from_coord)
            graph.add_vertex(to_id, to_coord)
            length = road_elem["properties"]["LENGTH"]
            direction = road_elem["properties"]["DIRECTION_OF_TRAFFIC_FLOW"]
            if direction in {"Both", "Positive"}:
                graph.add_edge_with_segments(from_id, to_id, {ogfid}, length, weight_type, id_to_segment_info[ogfid])
            if direction in {"Both", "Negative"}:
                graph.add_edge_with_segments(to_id, from_id, {ogfid}, length, weight_type, id_to_segment_info[ogfid])
    graph.add_message_to_vertices(vertices_of_interest)
    return graph


def read_prebuilt_graph(graph_file: TextIO, weight_type: str,
                        vertices_of_interest: dict[int, str], pruned_classes: set[str]) -> Optional[Graph]:
    """Read a prebuilt graph from a txt file.
    Return None if weight_type or vertices_of_interest is inconsistent with
    the pre-stored weight_type or vertices_of_interest.
    """
    stored_weight_type = graph_file.readline().strip()
    line = graph_file.readline().strip().split()
    stored_vertices = {int(s) for s in line}
    line = graph_file.readline().strip().split("|")
    stored_pruned_classes = {pruned_class for pruned_class in line}
    if stored_weight_type != weight_type or stored_vertices != set(vertices_of_interest.keys()) or \
            stored_pruned_classes != pruned_classes:
        return None
    else:
        graph = Graph()
        line = graph_file.readline().strip().split()
        assert line[0] == "V"
        vertex_count = int(line[1])
        for _ in range(vertex_count):
            cur_id = int(graph_file.readline().strip())
            line = graph_file.readline().strip().split()
            cur_lat, cur_lon = float(line[0]), float(line[1])
            message = ''
            if cur_id in vertices_of_interest:
                message = vertices_of_interest[cur_id]
            graph.add_vertex(cur_id, [cur_lat, cur_lon], message)
        line = graph_file.readline().strip().split()
        assert line[0] == "E"
        edges_count = int(line[1])
        line = graph_file.readline().strip().split()
        for _ in range(edges_count):
            assert line[0] == 'e'
            start_id, end_id = int(line[1]), int(line[2])
            line = graph_file.readline().strip().split()
            ogfids = {int(s) for s in line}
            line = graph_file.readline().strip().split()
            assert line[0] == 'd'
            dist = float(line[1])
            line = graph_file.readline().strip().split()
            assert line[0] == 't'
            time = float(line[1])
            line = graph_file.readline().strip().split()
            assert line[0] == "S"
            seg_info = []
            while line[0] == "S":
                corr_ogfid = int(line[1])
                seg_len = float(graph_file.readline().strip())
                rc = graph_file.readline().strip()
                speed_lim = int(graph_file.readline().strip())
                temp = graph_file.readline().strip().split()
                temp_coords = [c.split(",") for c in temp]
                coords = [[float(c[0]), float(c[1])] for c in temp_coords]
                road_name = graph_file.readline().strip()
                seg_info.append((corr_ogfid, seg_len, rc, speed_lim, coords, road_name))
                line = graph_file.readline().strip().split()
            graph.add_edge_with_segments(start_id, end_id, ogfids, dist, weight_type, seg_info)
            assert math.isclose(dist, graph.get_weight(start_id, end_id, "distance"), abs_tol=10)
            assert math.isclose(time, graph.get_weight(start_id, end_id, "travel_time"), abs_tol=1e-3)
        assert line[0] == "END"
        return graph
