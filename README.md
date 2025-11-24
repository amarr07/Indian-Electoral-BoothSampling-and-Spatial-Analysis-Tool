# 🗺️ Booth Mapping and Clustering Tool

A Streamlit-based web application for mapping and clustering election booth locations using geospatial analysis and machine learning.

## Overview

This tool helps analyze and select representative booth samples from Assembly Constituencies (AC) or Parliamentary Constituencies (PC) using KMeans clustering algorithms. It validates booth locations, creates clusters, and generates interactive maps with downloadable results.

## Features

- **State-wise Analysis**: Supports multiple Indian states with AC/PC level granularity
- **Intelligent Clustering**: Uses KMeans algorithm to create optimal booth clusters
- **Geospatial Validation**: Ensures all booths fall within their respective AC/PC boundaries
- **Interactive Maps**: Generate Folium-based HTML maps with color-coded clusters
- **Smart Selection**: Automatically selects 2 booths per cluster based on proximity to centroids
- **Export Options**: Download summary and detailed booth data as CSV files
- **Comprehensive UI**: User-friendly Streamlit interface with real-time processing

## Project Structure

```
booth_mapping_project/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── Data/                       # State-wise shapefiles
│   ├── <state>/
│   │   ├── <state>.assembly.shp       # Assembly constituency boundaries
│   │   ├── <state>.parliamentary.shp  # Parliamentary constituency boundaries
│   │   └── <state>.booth.shp          # Booth point locations
├── utils/                      # Utility modules
│   ├── __init__.py
│   ├── data_utils.py          # Data loading and validation functions
│   ├── clustering_utils.py    # KMeans clustering and booth selection
│   └── map_utils.py           # Folium map generation and styling
├── output/                     # Generated outputs
│   ├── maps/                  # HTML map files
│   ├── summary.csv            # Processing summary
│   └── selected_booths.csv    # Selected booth details
├── README.md                   # This file
└── instructions.md            # Detailed project instructions
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/amarr07/Indian-Electoral-Booth-Sampling-and-Spatial-Analysis-Tool.git
   cd Indian-Electoral-Booth-Sampling-and-Spatial-Analysis-Tool
   ```

2. **Download Electoral Data**:
   
   The shapefile data is too large for GitHub. Download it separately:
   
   - **Source**: [datameet/maps - Indian Electoral Boundaries](https://github.com/datameet/maps)
   - Download the `mapping-indias-elections` dataset
   - Extract the state folders into the `Data/` directory in the project root
   
   Expected structure:
   ```
   Data/
   ├── andhrapradesh/
   ├── assam/
   ├── bihar/
   └── ... (other states)
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Start the application**:
   ```bash
   streamlit run app.py
   ```

2. **Configure analysis**:
   - Select a state from the sidebar
   - Choose selection type (AC wise or PC wise)
   - Select specific AC/PC
   - Set number of samples per AC/PC (default: 300)

3. **Generate results**:
   - Click "Generate Results" button
   - View interactive map and statistics
   - Download CSV files and HTML maps

## Workflow

### 1. Data Loading
- Scans `Data/` directory for available states
- Loads AC/PC and booth shapefiles using GeoPandas
- Validates data and extracts geospatial information

### 2. Booth Validation
- Filters booths to ensure they fall within selected AC/PC polygon
- Uses Shapely's spatial operations for validation
- Extracts latitude/longitude coordinates

### 3. Clustering
- Calculates cluster count: `round(samples_per_ac / 25)`
- Applies KMeans clustering to booth coordinates
- Creates evenly distributed clusters across the AC/PC

### 4. Booth Selection
- For each cluster, finds booths near the centroid:
  - Primary range: 500m - 2km from centroid
  - Extended range: up to 3km if needed
- Selects 2 booths per cluster (closest to centroid)
- Marks as "Not completed" if insufficient booths found

### 5. Map Generation
- Creates interactive Folium maps with:
  - All booths color-coded by cluster
  - Cluster centroids marked with icons
  - Selected booths highlighted with star markers
- Saves maps as HTML files in `output/maps/`

### 6. Data Export
- **summary.csv**: Processing status and statistics per AC/PC
- **selected_booths.csv**: Detailed information for each selected booth

## Output Format

### Summary CSV Columns
- AC/PC code and name
- Total_Booths
- Selected_Booths
- Status (Completed/Not completed)
- Reason (if incomplete)
- Samples_Requested

### Selected Booths CSV Columns
- state
- district, district_n
- pc, pc_name
- ac, ac_name
- booth, booth_name
- cluster
- latitude, longitude

## Requirements

- Python 3.8+
- streamlit >= 1.28.0
- geopandas >= 0.14.0
- pandas >= 2.0.0
- numpy >= 1.24.0
- folium >= 0.14.0
- shapely >= 2.0.0
- geopy >= 2.4.0
- scikit-learn >= 1.3.0

## Data Format

Shapefiles should contain the following attributes (case-insensitive):

**AC/PC Shapefiles**:
- AC_NO/PC_NO or AC/PC (code)
- AC_NAME/PC_NAME (name)
- Polygon geometry

**Booth Shapefiles**:
- BOOTH_NO or BOOTH (booth code)
- BOOTH_NAME (booth name)
- AC_NO/PC_NO (constituency reference)
- DISTRICT, DISTRICT_N (district info)
- Point geometry

## Notes

- All spatial operations use latitude/longitude coordinates (EPSG:4326)
- Cluster count is automatically calculated based on sample size
- If total booths < samples requested, processing is marked as incomplete
- Maps use OpenStreetMap tiles by default
- Color palette supports up to 30 distinct cluster colors

## Troubleshooting

**No states showing up?**
- Ensure Data/ directory exists and contains state folders
- Check that shapefiles follow naming conventions

**Error loading shapefiles?**
- Verify all shapefile components exist (.shp, .shx, .dbf, .prj)
- Check file permissions

**Incomplete selections?**
- Reduce samples_per_ac value
- Check booth distribution in the selected AC/PC
- Review cluster configuration

## License

Please refer to Data/LICENSE.txt for data usage terms.

## Credits

Data Source: Election Commission of India
Built with: Streamlit, GeoPandas, Folium, scikit-learn
