import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.cluster import KMeans
from geopy.distance import geodesic
from typing import List, Tuple, Dict


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
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    booths_gdf['cluster'] = kmeans.fit_predict(coords)
    
    cluster_centers = kmeans.cluster_centers_
    
    return booths_gdf, cluster_centers


def find_booths_near_centroid(booths_gdf: gpd.GeoDataFrame, centroid: Tuple[float, float], 
                               cluster_id: int, max_booths: int = 2) -> List[int]:
    cluster_booths = booths_gdf[booths_gdf['cluster'] == cluster_id].copy()
    
    if cluster_booths.empty:
        return []
    
    distances = []
    indices = []
    
    for idx, row in cluster_booths.iterrows():
        booth_coord = (row['latitude'], row['longitude'])
        dist = geodesic(centroid, booth_coord).meters
        distances.append(dist)
        indices.append(idx)
    
    dist_df = pd.DataFrame({
        'index': indices,
        'distance': distances
    })
    
    dist_df = dist_df.sort_values('distance')
    
    preferred_range = dist_df[(dist_df['distance'] >= 500) & (dist_df['distance'] <= 2000)]
    
    if len(preferred_range) >= max_booths:
        selected = preferred_range.head(max_booths)
    else:
        extended_range = dist_df[(dist_df['distance'] >= 500) & (dist_df['distance'] <= 3000)]
        
        if len(extended_range) >= max_booths:
            selected = extended_range.head(max_booths)
        else:
            if len(extended_range) > 0:
                selected = extended_range.head(max_booths)
            else:
                selected = dist_df.head(max_booths)
    
    return selected['index'].tolist()


def select_booths_from_clusters(booths_gdf: gpd.GeoDataFrame, cluster_centers: np.ndarray, 
                                  booths_per_cluster: int = 2) -> Tuple[gpd.GeoDataFrame, bool, str]:
    selected_indices = []
    n_clusters = len(cluster_centers)
    
    incomplete_clusters = []
    
    for cluster_id in range(n_clusters):
        centroid = tuple(cluster_centers[cluster_id])
        
        booth_indices = find_booths_near_centroid(
            booths_gdf, centroid, cluster_id, max_booths=booths_per_cluster
        )
        
        if len(booth_indices) < booths_per_cluster:
            incomplete_clusters.append(cluster_id)
        
        selected_indices.extend(booth_indices)
    
    selected_booths = booths_gdf.loc[selected_indices].copy()
    
    is_complete = len(incomplete_clusters) == 0
    reason = ""
    
    if not is_complete:
        reason = f"Could not find {booths_per_cluster} booths within 3km for cluster(s): {incomplete_clusters}"
    
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
