import os
import folium
import geopandas as gpd
import numpy as np
from typing import Optional, List


CLUSTER_COLORS = [
    '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF',
    '#800000', '#008000', '#000080', '#808000', '#800080', '#008080',
    '#FFA500', '#A52A2A', '#DEB887', '#5F9EA0', '#7FFF00', '#D2691E',
    '#FF7F50', '#6495ED', '#DC143C', '#00FFFF', '#00008B', '#008B8B',
    '#B8860B', '#A9A9A9', '#006400', '#BDB76B', '#8B008B', '#556B2F'
]


def get_cluster_color(cluster_id: int) -> str:
    return CLUSTER_COLORS[cluster_id % len(CLUSTER_COLORS)]


def create_booth_map(booths_gdf: gpd.GeoDataFrame, selected_booths_gdf: gpd.GeoDataFrame,
                     cluster_centers: np.ndarray, ac_pc_name: str, ac_pc_code: str) -> folium.Map:
    if not booths_gdf.empty:
        center_lat = booths_gdf['latitude'].mean()
        center_lon = booths_gdf['longitude'].mean()
    else:
        center_lat, center_lon = 20.5937, 78.9629
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles='OpenStreetMap'
    )
    
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 400px; height: 60px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:16px; padding: 10px">
        <b>{ac_pc_name} ({ac_pc_code})</b><br>
        Total Booths: {len(booths_gdf)} | Selected: {len(selected_booths_gdf)}
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    if 'cluster' in booths_gdf.columns:
        for cluster_id in booths_gdf['cluster'].unique():
            cluster_booths = booths_gdf[booths_gdf['cluster'] == cluster_id]
            color = get_cluster_color(cluster_id)
            
            for idx, row in cluster_booths.iterrows():
                is_selected = idx in selected_booths_gdf.index if not selected_booths_gdf.empty else False
                
                popup_text = f"Cluster: {cluster_id}<br>"
                if 'booth' in row.index:
                    popup_text += f"Booth: {row['booth']}<br>"
                if 'booth_name' in row.index:
                    popup_text += f"Name: {row['booth_name']}<br>"
                popup_text += f"Lat: {row['latitude']:.6f}<br>Lon: {row['longitude']:.6f}"
                
                if is_selected:
                    folium.Marker(
                        location=[row['latitude'], row['longitude']],
                        popup=folium.Popup(popup_text, max_width=200),
                        icon=folium.Icon(color='red', icon='star', prefix='fa'),
                        tooltip=f"Selected - Cluster {cluster_id}"
                    ).add_to(m)
                else:
                    folium.CircleMarker(
                        location=[row['latitude'], row['longitude']],
                        radius=3,
                        popup=folium.Popup(popup_text, max_width=200),
                        color=color,
                        fill=True,
                        fillColor=color,
                        fillOpacity=0.6,
                        weight=1,
                        tooltip=f"Cluster {cluster_id}"
                    ).add_to(m)
    else:
        for idx, row in booths_gdf.iterrows():
            popup_text = ""
            if 'booth' in row.index:
                popup_text += f"Booth: {row['booth']}<br>"
            if 'booth_name' in row.index:
                popup_text += f"Name: {row['booth_name']}<br>"
            popup_text += f"Lat: {row['latitude']:.6f}<br>Lon: {row['longitude']:.6f}"
            
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=3,
                popup=folium.Popup(popup_text, max_width=200),
                color='blue',
                fill=True,
                fillColor='blue',
                fillOpacity=0.6,
                weight=1
            ).add_to(m)
    
    if cluster_centers is not None and len(cluster_centers) > 0:
        for cluster_id, center in enumerate(cluster_centers):
            color = get_cluster_color(cluster_id)
            folium.Marker(
                location=[center[0], center[1]],
                popup=f"Cluster {cluster_id} Center",
                icon=folium.Icon(color='black', icon='bullseye', prefix='fa'),
                tooltip=f"Cluster {cluster_id} Centroid"
            ).add_to(m)
    
    return m


def save_map(map_obj: folium.Map, output_path: str) -> bool:
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        map_obj.save(output_path)
        return True
    except Exception as e:
        print(f"Error saving map to {output_path}: {e}")
        return False


def create_and_save_map(booths_gdf: gpd.GeoDataFrame, selected_booths_gdf: gpd.GeoDataFrame,
                        cluster_centers: np.ndarray, ac_pc_name: str, ac_pc_code: str,
                        output_dir: str = "output/maps") -> tuple[folium.Map, str]:
    map_obj = create_booth_map(
        booths_gdf, selected_booths_gdf, cluster_centers, ac_pc_name, ac_pc_code
    )
    
    safe_name = ac_pc_name.replace(' ', '_').replace('/', '_')
    filename = f"{ac_pc_code}_{safe_name}_map.html"
    output_path = os.path.join(output_dir, filename)
    
    save_map(map_obj, output_path)
    
    return map_obj, output_path
