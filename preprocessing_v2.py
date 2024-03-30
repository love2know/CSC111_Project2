"""Improved version of preprocessing."""
from typing import TextIO
import json
import os
import webbrowser
from graph_utils_v2 import *


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
        if road_segment_type != "VIRTUAL_ROAD" and (road_segment_type == "FERRY CONNECTION" or speed_limit is not None):
            if speed_limit is None:
                speed_limit = 34
            ogfid = segment["properties"]["ROAD_NET_ELEMENT_ID"]
            name = segment["properties"]["FULL_STREET_NAME"]
            if name is None:
                name = ''
            length = segment["properties"]["LENGTH"]
            road_class = segment["properties"]["ROAD_CLASS"]
            coords = segment["geometry"]["coordinates"]
            if all(len(c) == 2 and isinstance(c[0], float) and isinstance(c[1], float) for c in coords):
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
                and all(isinstance(c, float) for c in from_coord) and \
                all(isinstance(c, float) for c in to_coord):
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
    road_graph.prune_graph(list(vertices_of_interest.keys()), {"Local / Street", "Local / Strata", "Local / Unknown"})
    print("pruning finished")
    print(f"{road_graph.vertex_count()} vertices, {road_graph.edge_count()} directed edges.")
    print("begin removing redundant vertices")
    road_graph.remove_redundant_vertices("travel_time", set(vertices_of_interest.keys()))
    print("removal finished")
    print(f"{road_graph.vertex_count()} vertices, {road_graph.edge_count()} directed edges.")
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
