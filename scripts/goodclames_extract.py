import pandas as pd
import numpy as np
from pathlib import Path

def load_good_claims():
    """Load the goodClaims.csv file and return as DataFrame"""
    csv_path = Path("data/Outputs/goodClaims.csv")
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found at {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    # Clean column names by removing leading/trailing spaces
    df.columns = df.columns.str.strip()
    
    print(f"Loaded {len(df)} claims from goodClaims.csv")
    print(f"Columns: {list(df.columns)}")
    return df

def filter_claims_by_location(df, target_lat, target_lon, radius_degrees=0.1):
    """
    Filter claims by latitude and longitude with optional radius
    
    Parameters:
    - df: DataFrame containing claims data
    - target_lat: Target latitude
    - target_lon: Target longitude  
    - radius_degrees: Search radius in degrees (default 0.1, approximately 11km)
    
    Returns:
    - Filtered DataFrame with claims within the specified radius
    """
    if df is None:
        df = load_good_claims()
    
    # Remove rows with missing coordinates
    df_clean = df.dropna(subset=['latitude', 'longitude'])
    
    # Calculate distance from target point
    lat_diff = df_clean['latitude'] - target_lat
    lon_diff = df_clean['longitude'] - target_lon
    distance = np.sqrt(lat_diff**2 + lon_diff**2)
    
    # Filter by radius
    filtered_df = df_clean[distance <= radius_degrees].copy()
    
    # Add distance column for reference
    filtered_df['distance_from_target'] = distance[distance <= radius_degrees]
    
    print(f"Found {len(filtered_df)} claims within {radius_degrees} degrees of ({target_lat}, {target_lon})")
    
    return filtered_df

def get_claims_by_exact_location(df, target_lat, target_lon, tolerance=0.001):
    """
    Get claims at exact or very close latitude/longitude coordinates
    
    Parameters:
    - df: DataFrame containing claims data
    - target_lat: Target latitude
    - target_lon: Target longitude
    - tolerance: Tolerance for exact match (default 0.001 degrees, ~100m)
    
    Returns:
    - DataFrame with claims at the exact location
    """
    if df is None:
        df = load_good_claims()
    
    # Remove rows with missing coordinates
    df_clean = df.dropna(subset=['latitude', 'longitude'])
    
    # Filter for exact location match
    exact_match = df_clean[
        (abs(df_clean['latitude'] - target_lat) <= tolerance) & 
        (abs(df_clean['longitude'] - target_lon) <= tolerance)
    ].copy()
    
    print(f"Found {len(exact_match)} claims at exact location ({target_lat}, {target_lon})")
    
    return exact_match

def get_claims_by_bounding_box(df, min_lat, max_lat, min_lon, max_lon):
    """
    Get claims within a bounding box defined by lat/lon limits
    
    Parameters:
    - df: DataFrame containing claims data
    - min_lat, max_lat: Latitude bounds
    - min_lon, max_lon: Longitude bounds
    
    Returns:
    - DataFrame with claims within the bounding box
    """
    if df is None:
        df = load_good_claims()
    
    # Remove rows with missing coordinates
    df_clean = df.dropna(subset=['latitude', 'longitude'])
    
    # Filter by bounding box
    bbox_filtered = df_clean[
        (df_clean['latitude'] >= min_lat) & 
        (df_clean['latitude'] <= max_lat) &
        (df_clean['longitude'] >= min_lon) & 
        (df_clean['longitude'] <= max_lon)
    ].copy()
    
    print(f"Found {len(bbox_filtered)} claims within bounding box")
    print(f"Lat: {min_lat} to {max_lat}, Lon: {min_lon} to {max_lon}")
    
    return bbox_filtered

def analyze_claims_risk(df):
    """
    Analyze risk indicators in the claims data
    
    Parameters:
    - df: DataFrame containing claims data
    
    Returns:
    - Dictionary with risk analysis summary
    """
    if df is None or len(df) == 0:
        return {"error": "No data to analyze"}
    
    analysis = {
        "total_claims": len(df),
        "claims_caused_by_100yr": len(df[df['causedBy100yr'] == 1]) if 'causedBy100yr' in df.columns else 0,
        "unique_flood_zones": df['floodZone'].value_counts().to_dict() if 'floodZone' in df.columns else {},
        "states_represented": df['state'].value_counts().to_dict() if 'state' in df.columns else {},
        "total_building_payout": df['amountPaidOnBuildingClaim'].sum() if 'amountPaidOnBuildingClaim' in df.columns else 0,
        "total_contents_payout": df['amountPaidOnContentsClaim'].sum() if 'amountPaidOnContentsClaim' in df.columns else 0,
        "elevated_buildings": len(df[df['elevatedBuildingIndicator'] == 1]) if 'elevatedBuildingIndicator' in df.columns else 0,
        "post_firm_construction": len(df[df['postFIRMConstructionIndicator'] == 1]) if 'postFIRMConstructionIndicator' in df.columns else 0
    }
    
    return analysis

# Example usage
if __name__ == "__main__":
    # Load the data
    claims_df = load_good_claims()
    
    # Example: Filter claims near Nashville, TN (36.1627, -86.7816)
    nashville_claims = filter_claims_by_location(claims_df, 36.1627, -86.7816, radius_degrees=0.5)
    
    # Analyze the filtered claims
    if len(nashville_claims) > 0:
        risk_analysis = analyze_claims_risk(nashville_claims)
        print("\nRisk Analysis for Nashville area:")
        for key, value in risk_analysis.items():
            print(f"{key}: {value}")