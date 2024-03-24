"""Preprocessing road data."""
from typing import TextIO
import json
import folium
import math
from graph_utils import RoadGraph


def data_to_graph(weight_criteria: str, road_element_data: TextIO, road_segment_data: TextIO) -> \
        RoadGraph:
    """Convert the road data into a graph.

    Preconditions:
        - weight_criteria in {'distance', 'travel_time'}
        - road_element_data and road_segment_data are the opened GeoJSON files
    """
    graph = RoadGraph()
    visited_roads = set()
    visited_connections = set()
    ogfid_to_info = {}
    edge_to_travel_time = {}
    edge_to_seg_len_sum = {}
    road_elements = json.load(road_element_data)
    road_segments = json.load(road_segment_data)
    elements = road_elements['features']
    segments = road_segments['features']
    for element in elements:
        ogfid = element['properties']['OGF_ID']
        direction = element['properties']['DIRECTION_OF_TRAFFIC_FLOW']
        length = element['properties']['LENGTH']
        start_junction_id = element['properties']['FROM_JUNCTION_ID']
        end_junction_id = element['properties']['TO_JUNCTION_ID']
        ogfid_to_info[ogfid] = ((start_junction_id, end_junction_id), length)
        start_coords = element['geometry']['coordinates'][0]
        end_coords = element['geometry']['coordinates'][-1]
        if any(not isinstance(c, float) for c in start_coords):
            print(ogfid)
            print(start_coords)
            continue
        if any(not isinstance(f, float) for f in end_coords):
            print(ogfid)
            print(end_coords)
            continue
        if start_junction_id not in graph:
            start_marker = folium.Marker(location=start_coords, popup=f'id: {start_junction_id}')
            graph.add_vertex(start_junction_id, start_marker)
        if end_junction_id not in graph:
            end_marker = folium.Marker(location=end_coords, popup=f'id: {end_junction_id}')
            graph.add_vertex(end_junction_id, end_marker)
        if start_junction_id != end_junction_id:
            if direction in {'Both', 'Positive'}:
                if (start_junction_id, end_junction_id) not in visited_connections:
                    visited_roads.add(ogfid)
                    graph.add_edge(start_junction_id, end_junction_id, length)
            if direction in {'Both', 'Negative'}:
                if (end_junction_id, start_junction_id) not in visited_connections:
                    visited_roads.add(ogfid)
                    graph.add_edge(end_junction_id, start_junction_id, length)
    for segment in segments:
        corr_ogfid = segment['properties']['ROAD_NET_ELEMENT_ID']
        if corr_ogfid in visited_roads:
            road_name = segment['properties']['FULL_STREET_NAME']
            seg_length = segment['properties']['LENGTH']
            speed_limit = segment['properties']['SPEED_LIMIT']
            coords = segment['geometry']['coordinates']
            poly_line = folium.PolyLine(locations=coords, popup=f'name: {road_name}\nlength: {seg_length}m\n'
                                                                f'speed limit: {speed_limit}')
            seg_direction = segment['properties']['DIRECTION_OF_TRAFFIC_FLOW']
            start_id, end_id = ogfid_to_info[corr_ogfid][0]
            if seg_direction in {'Both', 'Positive'}:
                graph.add_segment_to_edge(start_id, end_id, poly_line)
                if speed_limit is None:
                    if segment['properties']['ROAD_ELEMENT_TYPE'] not in {"VIRTUAL ROAD", "FERRY CONNECTION"}:
                        print(corr_ogfid)
                        print(segment['properties']['ROAD_ELEMENT_TYPE'])
                    # The only case where a speed limit data can be missing is when the road segment
                    # is a ferry connection.
                    dt = seg_length / 34e3
                    # Assume ferry speed is ~34km/h, which might be an overestimation in certain cases.
                else:
                    dt = seg_length / (speed_limit * 1e3)
                if (start_id, end_id) in edge_to_travel_time:
                    edge_to_travel_time[(start_id, end_id)] += dt
                    edge_to_seg_len_sum[(start_id, end_id)] += seg_length
                else:
                    edge_to_travel_time[(start_id, end_id)] = dt
                    edge_to_seg_len_sum[(start_id, end_id)] = seg_length
            if seg_direction in {'Both', 'Negative'}:
                graph.add_segment_to_edge(end_id, start_id, poly_line)
                if speed_limit is None:
                    if segment['properties']['ROAD_ELEMENT_TYPE'] not in {"VIRTUAL ROAD", "FERRY CONNECTION"}:
                        print(corr_ogfid)
                        print(segment['properties']['ROAD_ELEMENT_TYPE'])
                    dt = seg_length / 34e3
                else:
                    dt = seg_length / (speed_limit * 1e3)
                if (end_id, start_id) in edge_to_travel_time:
                    edge_to_travel_time[(end_id, start_id)] += dt
                    edge_to_seg_len_sum[(end_id, start_id)] += seg_length
                else:
                    edge_to_travel_time[(end_id, start_id)] = dt
                    edge_to_seg_len_sum[(end_id, start_id)] = seg_length
    print(len(edge_to_seg_len_sum))
    print(graph.edge_count())
    for start_id, end_id in edge_to_travel_time:
        assert math.isclose(edge_to_seg_len_sum[(start_id, end_id)], graph.get_weight(start_id, end_id)
                            , rel_tol=100)
        if weight_criteria == 'travel time':
            graph.update_weight(start_id, end_id, edge_to_travel_time[(start_id, end_id)])
    return graph


if __name__ == '__main__':
    road_graph: RoadGraph
    with open("data/ORN_Road_Elements.geojson") as road_elem_data, open("data/ORN_Segments.geojson") as road_seg_data:
        road_graph = data_to_graph('travel time', road_elem_data, road_seg_data)
    print(road_graph)
    road_map = road_graph.to_map()
    road_map.show_in_browser()
