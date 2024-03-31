"""Improved version of preprocessing."""
from typing import Optional, TextIO
import json
import os
import webbrowser
import math
import folium
from graph_utils_v2 import Graph


def data_to_graph_v2(road_elem_data: TextIO, segment_data: TextIO) -> Graph:
    """Construct a graph from the road element data and segmentation data.
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
                    id_to_segment_info[ogfid] = [(length, road_class, speed_limit, coords, name)]
                else:
                    id_to_segment_info[ogfid].append((length, road_class, speed_limit, coords, name))
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
                graph.add_edge(from_id, to_id, {ogfid}, length)
                for seg_len, rc, speed_lim, coordinates, road_name in id_to_segment_info[ogfid]:
                    graph.add_segment_to_edge(from_id, to_id, ogfid, seg_len, rc, speed_lim, coordinates, road_name)
            if direction in {"Both", "Negative"}:
                graph.add_edge(to_id, from_id, {ogfid}, length)
                for seg_len, rc, speed_lim, coordinates, road_name in id_to_segment_info[ogfid]:
                    graph.add_segment_to_edge(to_id, from_id, ogfid, seg_len, rc, speed_lim, coordinates, road_name)
    graph.update_travel_times()
    return graph


def data_to_graph_v3(road_elem_data: TextIO, segment_data: TextIO,
                     weight_type: str, vertices_of_interest: dict[int, str]) -> Graph:
    """Improved version of data_to_graph.

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


if __name__ == "__main__":
    road_graph: Graph
    with open('data/ORN_Road_Elements.geojson') as road_elem_data, open('data/ORN_Segments.geojson') as segment_data:
        road_graph = data_to_graph_v2(road_elem_data, segment_data)
    print("graph loading successful")
    vertices_of_interest = {6295901: "Rideau Canal",
                            6186776: "Accessible via ferry connection",
                            6514158: "Toronto Union Station",
                            5535850: "In the Niagara River below the cliff, there's a formidable whirlpool.",
                            1500062963: "Sioux Lookout Railway Station." +
                                        " This is an important settlement in Western Ontario",
                            5622840: "Just to check whether the algorithms work for a dead end.",
                            7166341: "Moose Factory National Historic Site. Accessible via winter road.",
                            3963316: "Fort Albany. Accessible via winter road.",
                            6070348: "Sudbury Station. It takes about 8 hrs for VIA Rail train No.1" +
                            " to travel from Toronto to here.",
                            7899949: "Marten Falls First Nation. Accessible via winter road."}
    road_graph.add_message_to_vertices(vertices_of_interest)
    print(f"{road_graph.vertex_count()} vertices, {road_graph.edge_count()} directed edges.")
    print("begin pruning")
    road_graph.prune_v2(set(vertices_of_interest.keys()), {"Local / Street", "Local / Strata", "Local / Unknown"})
    print("pruning finished")
    print(f"{road_graph.vertex_count()} vertices, {road_graph.edge_count()} directed edges.")
    print("begin removing redundant vertices")
    road_graph.remove_redundant_vertices("travel_time", set(vertices_of_interest.keys()))
    print("removal finished")
    print(f"{road_graph.vertex_count()} vertices, {road_graph.edge_count()} directed edges.")
    # vertex_lst = list(vertices_of_interest.keys())
    # for i in range(len(vertex_lst)):
    #     for j in range(len(vertex_lst)):
    #         if j != i:
    #             print(f"start_id: {vertex_lst[i]}, end_id: {vertex_lst[j]}")
    #             res = road_graph.find_shortest_path(vertex_lst[i], vertex_lst[j], "travel_time")
    #             if res is not None:
    #                 print(f"Expected travel time: {res[1]} hrs.")
    #             else:
    #                 print(f"No route exists.")
    road_graph.visualize_vertices(set(vertices_of_interest.keys()), "available_destinations.html")
    webbrowser.open_new_tab('file:///' + os.getcwd() + '/' + 'available_destinations.html')
    word = input("Enter 'q' to quit; Press enter to proceed to route planning. ")
    count = 0
    while word != 'q':
        count += 1
        start_id = int(input("Enter the id of the desired starting point: "))
        end_id = int(input("Enter the id of the desired destination: "))
        print("begin planning route")
        res = road_graph.find_shortest_path(start_id, end_id, "travel_time")
        print("finished planning route")
        if res is None:
            print("No route exists. ")
        else:
            path, cost = res
            road_graph.visualize_route(path, f"result_#{count}.html")
            print(f"The expected travel time is {cost} hours.")
            webbrowser.open_new_tab('file:///' + os.getcwd() + '/' + f"result_#{count}.html")
        word = input("Enter 'q' to quit; Press enter to proceed to planning the next route. ")

    # sample_map = folium.Map(location=[-56.0, -67.0])
    # mk = folium.Marker(location=[-56.0, -67.2])
    # folium.Popup("Cape Horn").add_to(mk)
    # sample_map.add_child(mk)
    # new_mk = folium.Marker(location=[55.0, -1.5], popup="Newcastle Upon Tyne")
    # sample_map.add_child(new_mk)
    # sample_map.save("sample_map.html")
    # webbrowser.open_new_tab('file:///'+os.getcwd()+'/' + 'sample_map.html')
    # word = input()
    # while word != 'q':
    #     print(word + ' happy')
    #     word = input()
