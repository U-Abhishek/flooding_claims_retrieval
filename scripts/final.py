import streamlit as st
import pandas as pd
import numpy as np
import ast
from geopy.distance import geodesic
import plotly.express as px
import plotly.graph_objects as go

def load_gage_data():
    """Load and parse the gage claims CSV data"""
    try:
        df = pd.read_csv("data/gage_claims_50km.csv")
        
        # Parse the string arrays into actual lists
        df['longitude'] = df['longitude'].apply(ast.literal_eval)
        df['latitude'] = df['latitude'].apply(ast.literal_eval)
        df['dates'] = df['dates'].apply(ast.literal_eval)
        df['num_claims'] = df['num_claims'].apply(ast.literal_eval)
        
        # Calculate center coordinates for each gauge
        df['center_lon'] = df['longitude'].apply(lambda x: np.mean(x) if x else np.nan)
        df['center_lat'] = df['latitude'].apply(lambda x: np.mean(x) if x else np.nan)
        
        # Calculate total claims per gauge
        df['total_claims'] = df['num_claims'].apply(lambda x: sum(x) if x else 0)
        
        # Calculate number of flood events per gauge
        df['num_events'] = df['dates'].apply(lambda x: len(x) if x else 0)
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def find_closest_gauges(df, target_lat, target_lon, max_distance_km=50):
    """Find gauges within specified distance of target coordinates"""
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Remove rows with missing center coordinates
    df_clean = df.dropna(subset=['center_lat', 'center_lon'])
    
    if df_clean.empty:
        return pd.DataFrame()
    
    # Calculate distances
    distances = []
    for _, row in df_clean.iterrows():
        try:
            distance = geodesic(
                (target_lat, target_lon), 
                (row['center_lat'], row['center_lon'])
            ).kilometers
            distances.append(distance)
        except:
            distances.append(np.inf)
    
    df_clean = df_clean.copy()
    df_clean['distance_km'] = distances
    
    # Filter by distance and sort
    nearby_gauges = df_clean[df_clean['distance_km'] <= max_distance_km].copy()
    nearby_gauges = nearby_gauges.sort_values('distance_km')
    
    return nearby_gauges

def create_claims_timeline(df):
    """Create a timeline of claims for visualization"""
    all_events = []
    
    for _, row in df.iterrows():
        if row['dates'] and row['num_claims']:
            for date, claims in zip(row['dates'], row['num_claims']):
                all_events.append({
                    'gauge_id': row['gauge_id'],
                    'date': pd.to_datetime(date),
                    'claims': claims,
                    'discharge': row['discharge'],
                    'distance_km': row.get('distance_km', 0)
                })
    
    if all_events:
        return pd.DataFrame(all_events)
    return pd.DataFrame()

def main():
    st.set_page_config(
        page_title="Flood Claims Analyzer",
        page_icon="🌊",
        layout="wide"
    )
    
    st.title("🌊 Flood Claims Analyzer")
    st.markdown("Find the closest USGS gauges and analyze flood claims data")
    
    # Load data
    with st.spinner("Loading gauge data..."):
        df = load_gage_data()
    
    if df is None:
        st.error("Failed to load data. Please check the CSV file.")
        return
    
    st.success(f"Loaded {len(df)} gauges with flood data")
    
    # Sidebar for input
    st.sidebar.header("📍 Location Input")
    
    # Input coordinates
    col1, col2 = st.sidebar.columns(2)
    with col1:
        target_lat = st.number_input(
            "Latitude", 
            min_value=-90.0, 
            max_value=90.0, 
            value=36.1627, 
            step=0.0001,
            format="%.4f"
        )
    
    with col2:
        target_lon = st.number_input(
            "Longitude", 
            min_value=-180.0, 
            max_value=180.0, 
            value=-86.7816, 
            step=0.0001,
            format="%.4f"
        )
    
    # Search radius
    max_distance = st.sidebar.slider(
        "Search Radius (km)", 
        min_value=1, 
        max_value=200, 
        value=50, 
        step=5
    )
    
    # Search button
    if st.sidebar.button("🔍 Find Closest Gauges", type="primary"):
        with st.spinner("Searching for nearby gauges..."):
            nearby_gauges = find_closest_gauges(df, target_lat, target_lon, max_distance)
            
            if nearby_gauges.empty:
                st.warning(f"No gauges found within {max_distance} km of the specified location.")
            else:
                st.session_state.nearby_gauges = nearby_gauges
                st.session_state.target_coords = (target_lat, target_lon)
    
    # Display results
    if 'nearby_gauges' in st.session_state:
        nearby_gauges = st.session_state.nearby_gauges
        target_lat, target_lon = st.session_state.target_coords
        
        st.header(f"📍 Results for ({target_lat:.4f}, {target_lon:.4f})")
        st.info(f"Found {len(nearby_gauges)} gauges within {max_distance} km")
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Gauges", len(nearby_gauges))
        with col2:
            total_claims = nearby_gauges['total_claims'].sum()
            st.metric("Total Claims", total_claims)
        with col3:
            total_events = nearby_gauges['num_events'].sum()
            st.metric("Total Events", total_events)
        with col4:
            avg_discharge = nearby_gauges['discharge'].mean()
            st.metric("Avg Discharge (cfs)", f"{avg_discharge:.0f}")
        
        # Detailed table
        st.subheader("📊 Gauge Details")
        
        # Prepare display data
        display_data = nearby_gauges[['gauge_id', 'distance_km', 'discharge', 'sqmi', 
                                    'total_claims', 'num_events']].copy()
        display_data['distance_km'] = display_data['distance_km'].round(2)
        display_data['discharge'] = display_data['discharge'].round(0)
        display_data['sqmi'] = display_data['sqmi'].round(4)
        
        st.dataframe(
            display_data,
            column_config={
                "gauge_id": "Gauge ID",
                "distance_km": "Distance (km)",
                "discharge": "Discharge (cfs)",
                "sqmi": "Watershed (sq mi)",
                "total_claims": "Total Claims",
                "num_events": "Flood Events"
            },
            use_container_width=True
        )
        
        # Claims timeline
        if nearby_gauges['total_claims'].sum() > 0:
            st.subheader("📅 Claims Timeline")
            
            timeline_df = create_claims_timeline(nearby_gauges)
            
            if not timeline_df.empty:
                # Timeline chart
                fig = px.scatter(
                    timeline_df, 
                    x='date', 
                    y='claims',
                    size='discharge',
                    color='gauge_id',
                    hover_data=['distance_km'],
                    title="Flood Claims Over Time",
                    labels={'date': 'Date', 'claims': 'Number of Claims'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # Detailed events table
                st.subheader("📋 Detailed Events")
                events_display = timeline_df.copy()
                events_display['date'] = events_display['date'].dt.strftime('%Y-%m-%d')
                events_display['discharge'] = events_display['discharge'].round(0)
                events_display['distance_km'] = events_display['distance_km'].round(2)
                
                st.dataframe(
                    events_display[['gauge_id', 'date', 'claims', 'discharge', 'distance_km']],
                    column_config={
                        "gauge_id": "Gauge ID",
                        "date": "Date",
                        "claims": "Claims",
                        "discharge": "Discharge (cfs)",
                        "distance_km": "Distance (km)"
                    },
                    use_container_width=True
                )
            else:
                st.info("No flood events found for the selected gauges.")
        
        # Map visualization
        if len(nearby_gauges) > 0:
            st.subheader("🗺️ Map View")
            
            # Create map
            fig = go.Figure()
            
            # Add target location
            fig.add_trace(go.Scattermapbox(
                lat=[target_lat],
                lon=[target_lon],
                mode='markers',
                marker=dict(size=15, color='red', symbol='star'),
                name='Target Location',
                text=['Your Location'],
                hovertemplate='<b>Target Location</b><br>Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<extra></extra>'
            ))
            
            # Add gauge locations
            fig.add_trace(go.Scattermapbox(
                lat=nearby_gauges['center_lat'],
                lon=nearby_gauges['center_lon'],
                mode='markers',
                marker=dict(
                    size=nearby_gauges['total_claims'] + 5,
                    color=nearby_gauges['discharge'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Discharge (cfs)")
                ),
                name='Gauges',
                text=nearby_gauges['gauge_id'],
                hovertemplate='<b>Gauge %{text}</b><br>Claims: %{marker.size}<br>Distance: %{customdata:.1f} km<extra></extra>',
                customdata=nearby_gauges['distance_km']
            ))
            
            fig.update_layout(
                mapbox=dict(
                    style="open-street-map",
                    center=dict(lat=target_lat, lon=target_lon),
                    zoom=8
                ),
                height=500,
                margin=dict(r=0, t=0, l=0, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("**Data Source**: USGS Gauge Data with Flood Claims Analysis")

if __name__ == "__main__":
    main()
