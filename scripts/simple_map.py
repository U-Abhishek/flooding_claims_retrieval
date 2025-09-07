import scipy.io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def load_gage_data():
    """Load and extract gage data from keptGages.mat"""
    mat_file = "data/Outputs/keptGages.mat"
    mat_data = scipy.io.loadmat(mat_file)
    kept_gages = mat_data['keptGages']
    
    print(f"Found {len(kept_gages)} records in .mat file")
    
    # Extract data
    extracted_data = []
    success_count = 0
    error_count = 0
    
    for i in range(len(kept_gages)):
        record = kept_gages[i][0]
        try:
            # Handle different data structures
            site_no = record['SITE_NO'][0] if record['SITE_NO'].size > 0 else f"unknown_{i}"
            
            # Handle SQMI - could be scalar or array
            if record['SQMI'].size == 1:
                sqmi = float(record['SQMI'][0][0]) if record['SQMI'].ndim > 1 else float(record['SQMI'][0])
            else:
                sqmi = float(record['SQMI'][0][0])
            
            # Handle ABS_DIFF - could be scalar or array
            if record['ABS_DIFF'].size == 1:
                abs_diff = float(record['ABS_DIFF'][0][0]) if record['ABS_DIFF'].ndim > 1 else float(record['ABS_DIFF'][0])
            else:
                abs_diff = float(record['ABS_DIFF'][0][0])
            
            # Get center coordinates from bounding box
            bbox = record['BoundingBox'][0]
            center_lon = (bbox[0][0] + bbox[1][0]) / 2
            center_lat = (bbox[0][1] + bbox[1][1]) / 2
            
            # Handle coordinate count
            coord_count = record['X'][0].size if record['X'].size > 0 else 0
            
            extracted_data.append({
                'site_no': site_no,
                'sqmi': sqmi,
                'abs_diff': abs_diff,
                'center_lon': center_lon,
                'center_lat': center_lat,
                'bbox_min_lon': bbox[0][0],
                'bbox_max_lon': bbox[1][0],
                'bbox_min_lat': bbox[0][1],
                'bbox_max_lat': bbox[1][1],
                'coord_count': coord_count
            })
            success_count += 1
            
        except Exception as e:
            error_count += 1
            if error_count <= 5:  # Only show first 5 errors
                print(f"Error extracting record {i}: {e}")
            continue
    
    print(f"Successfully extracted {success_count} records, {error_count} errors")
    
    df = pd.DataFrame(extracted_data)
    if not df.empty:
        print(f"DataFrame created with {len(df)} rows and columns: {list(df.columns)}")
    else:
        print("Warning: No data extracted!")
    
    return df

def create_gage_map(df):
    """Create a comprehensive map showing gage locations and coverage"""
    
    if df.empty:
        print("Error: No data available to create map")
        return
    
    # Filter out invalid data
    valid_df = df[(df['sqmi'] > 0) & (df['center_lon'] != 0) & (df['center_lat'] != 0)]
    
    if valid_df.empty:
        print("Error: No valid data after filtering")
        return
    
    print(f"Creating map with {len(valid_df)} valid gage records")
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # Plot gage locations with size based on drainage area and color based on quality
    scatter = ax.scatter(valid_df['center_lon'], valid_df['center_lat'], 
                        s=valid_df['sqmi'] * 0.5,  # Size proportional to drainage area
                        c=valid_df['abs_diff'],     # Color based on quality metric
                        alpha=0.7, 
                        cmap='viridis',
                        edgecolors='black',
                        linewidth=0.5)
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
    cbar.set_label('ABS_DIFF (Quality Metric)', fontsize=12)
    
    # Set labels and title
    ax.set_xlabel('Longitude', fontsize=14)
    ax.set_ylabel('Latitude', fontsize=14)
    ax.set_title(f'USGS Gage Locations and Coverage Areas\n'
                f'Size = Drainage Area (sq mi), Color = Analysis Quality\n'
                f'Total Gages: {len(valid_df):,}', fontsize=16)
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    # Add some statistics as text
    stats_text = f"""Statistics:
• Drainage Area Range: {valid_df['sqmi'].min():.1f} - {valid_df['sqmi'].max():.1f} sq mi
• Quality Range: {valid_df['abs_diff'].min():.6f} - {valid_df['abs_diff'].max():.6f}
• Geographic Coverage:
  Longitude: {valid_df['center_lon'].min():.2f}° to {valid_df['center_lon'].max():.2f}°
  Latitude: {valid_df['center_lat'].min():.2f}° to {valid_df['center_lat'].max():.2f}°"""
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=dict(boxstyle="round,pad=0.5", 
            facecolor="white", alpha=0.8))
    
    # Add legend for size
    sizes = [100, 1000, 5000, 10000]  # Example drainage areas
    labels = [f'{s} sq mi' for s in sizes]
    legend_elements = [plt.scatter([], [], s=s*0.5, c='gray', alpha=0.7, 
                                 edgecolors='black', linewidth=0.5, label=label) 
                      for s, label in zip(sizes, labels)]
    
    ax.legend(handles=legend_elements, title='Drainage Area', 
             loc='lower right', fontsize=10)
    
    plt.tight_layout()
    
    # Save the plot
    output_file = "data/Outputs/gage_map.png"
    Path("data/Outputs").mkdir(exist_ok=True)
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Map saved to {output_file}")
    
    plt.show()

def main():
    """Main function"""
    print("Loading gage data...")
    df = load_gage_data()
    print(f"Loaded {len(df)} total records")
    
    print("Creating gage map...")
    create_gage_map(df)

if __name__ == "__main__":
    main()
