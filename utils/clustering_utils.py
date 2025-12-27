import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.cluster import KMeans
from geopy.distance import geodesic
from typing import List, Tuple, Dict
import random


def calculate_cluster_count(samples_per_ac: int) -> int:
    return round(samples_per_ac / 25)


def cluster_booths(booths_gdf: gpd.GeoDataFrame, n_clusters: int) -> Tuple[gpd.GeoDataFrame, np.ndarray]:
    if booths_gdf is None or booths_gdf.empty:
        return booths_gdf, np.array([])
    
    if 'latitude' not in booths_gdf.columns or 'longitude' not in booths_gdf.columns:
        return booths_gdf, np.array([])
    
    coords = booths_gdf[['latitude', 'longitude']].values
    
    n_clusters = min(n_clusters, len(coords))
    
    if n_clusters < 1:
        return booths_gdf, np.array([])
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=None, n_init=10)
    booths_gdf['cluster'] = kmeans.fit_predict(coords)
    
    cluster_centers = kmeans.cluster_centers_
    
    return booths_gdf, cluster_centers


def find_booths_near_centroid(booths_gdf: gpd.GeoDataFrame, centroid: Tuple[float, float], 
                               cluster_id: int, max_booths: int = 2) -> List[int]:
    cluster_booths = booths_gdf[booths_gdf['cluster'] == cluster_id].copy()
    
    if cluster_booths.empty:
        return []
    
    if len(cluster_booths) < max_booths:
        return cluster_booths.index.tolist()
    
    booth_coords = {}
    for idx, row in cluster_booths.iterrows():
        booth_coords[idx] = (row['latitude'], row['longitude'])
    
    valid_pairs = []
    indices_list = list(booth_coords.keys())
    
    for i in range(len(indices_list)):
        for j in range(i + 1, len(indices_list)):
            idx1, idx2 = indices_list[i], indices_list[j]
            coord1, coord2 = booth_coords[idx1], booth_coords[idx2]
            distance = geodesic(coord1, coord2).meters
            
            if 500 <= distance <= 2000:
                valid_pairs.append((idx1, idx2, distance))
    
    if valid_pairs:
        selected_pair = random.choice(valid_pairs)
        return [selected_pair[0], selected_pair[1]]
    
    extended_pairs = []
    for i in range(len(indices_list)):
        for j in range(i + 1, len(indices_list)):
            idx1, idx2 = indices_list[i], indices_list[j]
            coord1, coord2 = booth_coords[idx1], booth_coords[idx2]
            distance = geodesic(coord1, coord2).meters
            
            if 500 <= distance <= 3000:
                extended_pairs.append((idx1, idx2, distance))
    
    if extended_pairs:
        selected_pair = random.choice(extended_pairs)
        return [selected_pair[0], selected_pair[1]]
    
    if len(indices_list) >= max_booths:
        return random.sample(indices_list, max_booths)
    else:
        return indices_list


def select_booths_from_clusters(booths_gdf: gpd.GeoDataFrame, cluster_centers: np.ndarray, 
                                  booths_per_cluster: int = 2) -> Tuple[gpd.GeoDataFrame, bool, str]:
    selected_indices = []
    n_clusters = len(cluster_centers)
    
    incomplete_clusters = []
    clusters_with_insufficient_booths = []
    
    actual_clusters_in_data = booths_gdf['cluster'].nunique()
    
    for cluster_id in range(n_clusters):
        centroid = tuple(cluster_centers[cluster_id])
        
        booth_indices = find_booths_near_centroid(
            booths_gdf, centroid, cluster_id, max_booths=booths_per_cluster
        )
        
        if len(booth_indices) == 0:
            incomplete_clusters.append(cluster_id)
        elif len(booth_indices) < booths_per_cluster:
            clusters_with_insufficient_booths.append((cluster_id, len(booth_indices)))
        
        selected_indices.extend(booth_indices)
    
    selected_booths = booths_gdf.loc[selected_indices].copy()
    
    is_complete = (len(incomplete_clusters) == 0 and 
                   len(clusters_with_insufficient_booths) == 0 and 
                   actual_clusters_in_data == n_clusters)
    
    reasons = []
    if actual_clusters_in_data < n_clusters:
        reasons.append(f"Only {actual_clusters_in_data}/{n_clusters} clusters formed")
    if len(incomplete_clusters) > 0:
        reasons.append(f"No booths found in cluster(s): {incomplete_clusters}")
    if len(clusters_with_insufficient_booths) > 0:
        insufficient_details = [f"cluster {c}({b} booth)" for c, b in clusters_with_insufficient_booths]
        reasons.append(f"Insufficient booths in: {', '.join(insufficient_details)}")
    
    reason = "; ".join(reasons) if reasons else ""
    
    return selected_booths, is_complete, reason


def process_ac_pc_clustering(booths_gdf: gpd.GeoDataFrame, samples_per_ac: int) -> Dict:
    total_booths = len(booths_gdf)
    
    n_clusters = calculate_cluster_count(samples_per_ac)
    
    if n_clusters < 1:
        return {
            'total_booths': total_booths,
            'selected_booths': gpd.GeoDataFrame(),
            'is_complete': False,
            'reason': 'Insufficient samples requested for clustering (minimum 25)',
            'cluster_centers': np.array([]),
            'clustered_booths': booths_gdf
        }
    
    if total_booths < n_clusters:
        return {
            'total_booths': total_booths,
            'selected_booths': gpd.GeoDataFrame(),
            'is_complete': False,
            'reason': f'Total booths ({total_booths}) < Required clusters ({n_clusters})',
            'cluster_centers': np.array([]),
            'clustered_booths': booths_gdf
        }
    
    clustered_booths, cluster_centers = cluster_booths(booths_gdf, n_clusters)
    
    selected_booths, is_complete, reason = select_booths_from_clusters(
        clustered_booths, cluster_centers, booths_per_cluster=2
    )
    
    return {
        'total_booths': total_booths,
        'selected_booths': selected_booths,
        'is_complete': is_complete,
        'reason': reason,
        'cluster_centers': cluster_centers,
        'clustered_booths': clustered_booths
    }
