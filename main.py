"""The main module."""
from typing import Optional, TextIO
from preprocessing import data_to_graph, read_prebuilt_graph
from graph_utils import Graph
import folium
import webbrowser
import os

SELECTED_DESTINATIONS = {6295901: "Rideau Canal",
                         6514158: "Toronto Union Station",
                         5535850: "Niagara Falls Whirlpool Aero Car",
                         1500062963: "Sioux Lookout Railway Station",
                         5622840: "A place in Kenora",
                         7166341: "Moose Factory National Historic Site. Accessible via winter road.",
                         3963316: "Fort Albany. Accessible via winter road.",
                         6070348: "Sudbury Railway Station",
                         7899949: "Marten Falls First Nation. Accessible via winter road.",
                         4360362: "Canada's Wonderland",
                         7609145: "Fort York National Historic Site",
                         6136355: "Tricky position 1",
                         4181412: "Windsor Railway Station",
                         5685552: "Tricky position 2",
                         5692111: "Tricky position 3",
                         4175727: "Tricky position 4",
                         4175230: "Tricky position 5",
                         6039549: "Tricky position 6",
                         1509660794: "Tricky position 7",
                         1500301341: "Tricky position 8",
                         5723053: "Tricky position 9",
                         5727850: "Tricky position 10",
                         1500202822: "Battle Hill National Historic Site",
                         7367553: "Thunder Bay Yacht Club",
                         4547920: "Rushing River Provincial Park",
                         7659327: "Kingston Railway Station",
                         1500162413: "Point Clark Lighthouse National Historic Site",
                         1500144236: "Kingston Harbour",
                         3576325: "Trent-Severn Waterway National Historic Site",
                         6043947: "Casa Loma"}

PRUNED_CLASSES = {"Local / Street", "Local / Strata", "Local / Unknown"}


if __name__ == "__main__":
    road_graph = None
    weight_type = ''
    while weight_type not in {"distance", "travel_time", "q"}:
        weight_type = input("Press 'q' to quite. What do you want to minimize? Enter 'distance' or 'travel_time': ")
        if weight_type not in {"distance", "travel_time", "q"}:
            print("Invalid input.")
    if weight_type != "q":
        if os.path.exists(f"{weight_type}_weighted_graph.txt"):
            print("Begin loading pre-pruned graph. This might take a while...")
            with open(f"{weight_type}_weighted_graph.txt", "r") as graph_file:
                road_graph = read_prebuilt_graph(graph_file, weight_type, SELECTED_DESTINATIONS, PRUNED_CLASSES)
            if road_graph is not None:
                print(f"Finished loading pre-pruned graph. "
                      f"{road_graph.vertex_count()} vertices, {road_graph.edge_count()} directed edges.")
            else:
                print("Graph configuration changed.")
        if not os.path.exists(f"{weight_type}_weighted_graph.txt") or road_graph is None:
            print("Graph needs to be constructed from scratch.")
            with open("data/ORN_Road_Elements.geojson", "r") as road_elem_data, \
                    open("data/ORN_Segments.geojson", "r") as segment_data:
                print("Begin loading graph. This might take a while...")
                road_graph = data_to_graph(road_elem_data, segment_data,
                                           weight_type, SELECTED_DESTINATIONS)
            print(f"Finished loading graph. "
                  f"{road_graph.vertex_count()} vertices, {road_graph.edge_count()} directed edges. ")
            print("Begin pruning graph. This might take a while...")
            road_graph.prune_graph(set(SELECTED_DESTINATIONS.keys()), PRUNED_CLASSES)
            print(f"Finished pruning graph. "
                  f"{road_graph.vertex_count()} vertices, {road_graph.edge_count()} directed edges. "
                  f"Begin removing redundant vertices.")
            road_graph.remove_redundant_vertices(weight_type, set(SELECTED_DESTINATIONS.keys()))
            print(f"Finished removing redundant vertices. "
                  f"{road_graph.vertex_count()} vertices, {road_graph.edge_count()} directed edges. "
                  f"Begin saving graph.")
            with open(f"{weight_type}_weighted_graph.txt", "w") as output_file:
                road_graph.write_graph(output_file, weight_type,
                                       list(SELECTED_DESTINATIONS.keys()), PRUNED_CLASSES)
            print("Finished saving graph.")
        road_graph.visualize_vertices(set(SELECTED_DESTINATIONS.keys()), "available_destinations.html")
        webbrowser.open_new_tab("file:///" + os.getcwd() + "/available_destinations.html")
        word = input("Enter 'q' to quit. Press enter to proceed to route planning: ")
        count = 0
        while word != 'q':
            start_id = int(input("Enter the id of the starting point: "))
            end_id = int(input("Enter the id of the destination point: "))
            if start_id in road_graph and end_id in road_graph:
                count += 1
                print("Begin planning route.")
                res = road_graph.find_shortest_path(start_id, end_id, weight_type)
                print("Finished planning route.")
                if res is not None:
                    path, cost = res
                    road_graph.visualize_route(path, f"result_#{count}.html")
                    webbrowser.open_new_tab("file:///" + os.getcwd() + f"/result_#{count}.html")
                    if weight_type == "distance":
                        print(f"The distance from the starting point to the destination is {round(cost / 1e3, 3)}km.")
                    else:
                        print(f"The expected travel time is {round(cost, 3)} hours.")
                else:
                    print("No route exist.")
            else:
                print("Invalid input.")
            word = input("Enter 'q' to quit. Press enter to proceed to the next route planning: ")
