import scipy.io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def load_gage_data():
    """Load and extract gage data from keptGages.mat"""
    mat_file = "data/Outputs/keptGages.mat"
    mat_data = scipy.io.loadmat(mat_file)
    kept_gages = mat_data['keptGages']
    
    # Extract data
    extracted_data = []
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
        except Exception as e:
            print(f"Error extracting record {i}: {e}")
            # Try to extract at least basic info
            try:
                site_no = f"error_{i}"
                sqmi = 0.0
                abs_diff = 0.0
                center_lon = 0.0
                center_lat = 0.0
                
                extracted_data.append({
                    'site_no': site_no,
                    'sqmi': sqmi,
                    'abs_diff': abs_diff,
                    'center_lon': center_lon,
                    'center_lat': center_lat,
                    'bbox_min_lon': 0.0,
                    'bbox_max_lon': 0.0,
                    'bbox_min_lat': 0.0,
                    'bbox_max_lat': 0.0,
                    'coord_count': 0
                })
            except:
                continue
    
    return pd.DataFrame(extracted_data)

def plot_gage_locations(df):
    """Plot gage locations on a map"""
    plt.figure(figsize=(12, 8))
    
    # Create scatter plot
    scatter = plt.scatter(df['center_lon'], df['center_lat'], 
                         c=df['sqmi'], s=df['abs_diff']*10000, 
                         alpha=0.6, cmap='viridis')
    
    plt.colorbar(scatter, label='Drainage Area (sq mi)')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('USGS Gage Locations\n(Size = ABS_DIFF, Color = Drainage Area)')
    plt.grid(True, alpha=0.3)
    
    # Add some statistics
    plt.figtext(0.02, 0.02, f'Total Gages: {len(df):,}\n'
                           f'Drainage Area Range: {df["sqmi"].min():.1f} - {df["sqmi"].max():.1f} sq mi\n'
                           f'ABS_DIFF Range: {df["abs_diff"].min():.6f} - {df["abs_diff"].max():.6f}',
                fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('data/Outputs/gage_locations.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_drainage_area_distribution(df):
    """Plot distribution of drainage areas"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Filter out zero values
    valid_sqmi = df[df['sqmi'] > 0]['sqmi']
    
    # Histogram
    ax1.hist(valid_sqmi, bins=50, alpha=0.7, color='skyblue', edgecolor='bqlack')
    ax1.set_xlabel('Drainage Area (sq mi)')
    ax1.set_ylabel('Number of Gages')
    ax1.set_title(f'Distribution of Drainage Areas\n(Valid records: {len(valid_sqmi):,})')
    ax1.grid(True, alpha=0.3)
    
    # Log scale histogram (only for positive values)
    if len(valid_sqmi) > 0:
        ax2.hist(np.log10(valid_sqmi), bins=50, alpha=0.7, color='lightcoral', edgecolor='black')
        ax2.set_xlabel('Log10(Drainage Area)')
        ax2.set_ylabel('Number of Gages')
        ax2.set_title('Distribution of Drainage Areas (Log Scale)')
        ax2.grid(True, alpha=0.3)
    else:
        ax2.text(0.5, 0.5, 'No valid drainage area data', ha='center', va='center', transform=ax2.transAxes)
        ax2.set_title('Distribution of Drainage Areas (Log Scale)')
    
    plt.tight_layout()
    plt.savefig('data/Outputs/drainage_area_distribution.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_quality_metrics(df):
    """Plot ABS_DIFF quality metrics"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Filter out zero values for meaningful analysis
    valid_data = df[(df['sqmi'] > 0) & (df['abs_diff'] > 0)]
    
    # Histogram of ABS_DIFF
    ax1.hist(df['abs_diff'], bins=50, alpha=0.7, color='lightgreen', edgecolor='black')
    ax1.set_xlabel('ABS_DIFF')
    ax1.set_ylabel('Number of Gages')
    ax1.set_title(f'Distribution of ABS_DIFF Values\n(Total records: {len(df):,})')
    ax1.grid(True, alpha=0.3)
    
    # Scatter plot: ABS_DIFF vs Drainage Area (only valid data)
    if len(valid_data) > 0:
        scatter = ax2.scatter(valid_data['sqmi'], valid_data['abs_diff'], alpha=0.6, c=valid_data['center_lat'], cmap='coolwarm')
        ax2.set_xlabel('Drainage Area (sq mi)')
        ax2.set_ylabel('ABS_DIFF')
        ax2.set_title(f'ABS_DIFF vs Drainage Area\n(Color = Latitude, Valid records: {len(valid_data):,})')
        ax2.set_xscale('log')
        plt.colorbar(scatter, ax=ax2, label='Latitude')
        ax2.grid(True, alpha=0.3)
    else:
        ax2.text(0.5, 0.5, 'No valid data for correlation', ha='center', va='center', transform=ax2.transAxes)
        ax2.set_title('ABS_DIFF vs Drainage Area')
    
    plt.tight_layout()
    plt.savefig('data/Outputs/quality_metrics.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_geographic_coverage(df):
    """Plot geographic coverage and density"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Geographic extent
    ax1.scatter(df['center_lon'], df['center_lat'], alpha=0.5, s=1, color='blue')
    ax1.set_xlabel('Longitude')
    ax1.set_ylabel('Latitude')
    ax1.set_title('Geographic Coverage of USGS Gages')
    ax1.grid(True, alpha=0.3)
    
    # Add bounding box
    ax1.add_patch(plt.Rectangle((df['bbox_min_lon'].min(), df['bbox_min_lat'].min()),
                               df['bbox_max_lon'].max() - df['bbox_min_lon'].min(),
                               df['bbox_max_lat'].max() - df['bbox_min_lat'].min(),
                               fill=False, color='red', linewidth=2, label='Total Coverage'))
    ax1.legend()
    
    # Density plot
    ax2.hexbin(df['center_lon'], df['center_lat'], gridsize=50, cmap='YlOrRd')
    ax2.set_xlabel('Longitude')
    ax2.set_ylabel('Latitude')
    ax2.set_title('Gage Density Heatmap')
    
    plt.tight_layout()
    plt.savefig('data/Outputs/geographic_coverage.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_summary_dashboard(df):
    """Create a comprehensive summary dashboard"""
    fig = plt.figure(figsize=(16, 12))
    
    # Create a grid layout
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # 1. Gage locations (top row, spans 2 columns)
    ax1 = fig.add_subplot(gs[0, :2])
    scatter = ax1.scatter(df['center_lon'], df['center_lat'], 
                         c=df['sqmi'], s=20, alpha=0.6, cmap='viridis')
    ax1.set_xlabel('Longitude')
    ax1.set_ylabel('Latitude')
    ax1.set_title('Gage Locations (Color = Drainage Area)')
    plt.colorbar(scatter, ax=ax1, label='Drainage Area (sq mi)')
    
    # 2. Drainage area distribution (top right)
    ax2 = fig.add_subplot(gs[0, 2])
    valid_sqmi = df[df['sqmi'] > 0]['sqmi']
    if len(valid_sqmi) > 0:
        ax2.hist(valid_sqmi, bins=30, alpha=0.7, color='skyblue')
        ax2.set_xlabel('Drainage Area (sq mi)')
        ax2.set_ylabel('Count')
        ax2.set_title(f'Drainage Area Distribution\n(Valid: {len(valid_sqmi):,})')
        ax2.set_yscale('log')
    else:
        ax2.text(0.5, 0.5, 'No valid data', ha='center', va='center', transform=ax2.transAxes)
        ax2.set_title('Drainage Area Distribution')
    
    # 3. ABS_DIFF distribution (middle left)
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.hist(df['abs_diff'], bins=30, alpha=0.7, color='lightgreen')
    ax3.set_xlabel('ABS_DIFF')
    ax3.set_ylabel('Count')
    ax3.set_title('Quality Metric Distribution')
    
    # 4. ABS_DIFF vs Drainage Area (middle center)
    ax4 = fig.add_subplot(gs[1, 1])
    valid_data = df[(df['sqmi'] > 0) & (df['abs_diff'] > 0)]
    if len(valid_data) > 0:
        ax4.scatter(valid_data['sqmi'], valid_data['abs_diff'], alpha=0.5, s=10)
        ax4.set_xlabel('Drainage Area (sq mi)')
        ax4.set_ylabel('ABS_DIFF')
        ax4.set_title(f'Quality vs Drainage Area\n(Valid: {len(valid_data):,})')
        ax4.set_xscale('log')
    else:
        ax4.text(0.5, 0.5, 'No valid data', ha='center', va='center', transform=ax4.transAxes)
        ax4.set_title('Quality vs Drainage Area')
    
    # 5. Coordinate count distribution (middle right)
    ax5 = fig.add_subplot(gs[1, 2])
    ax5.hist(df['coord_count'], bins=30, alpha=0.7, color='orange')
    ax5.set_xlabel('Coordinate Count')
    ax5.set_ylabel('Count')
    ax5.set_title('Watershed Complexity')
    
    # 6. Summary statistics (bottom row)
    ax6 = fig.add_subplot(gs[2, :])
    ax6.axis('off')
    
    # Create summary text
    summary_text = f"""
    SUMMARY STATISTICS
    Total Gages: {len(df):,}
    Unique Site Numbers: {df['site_no'].nunique():,}
    
    Drainage Area (sq mi):
      Min: {df['sqmi'].min():.2f}
      Max: {df['sqmi'].max():.2f}
      Mean: {df['sqmi'].mean():.2f}
      Median: {df['sqmi'].median():.2f}
    
    ABS_DIFF (Quality Metric):
      Min: {df['abs_diff'].min():.6f}
      Max: {df['abs_diff'].max():.6f}
      Mean: {df['abs_diff'].mean():.6f}
      Median: {df['abs_diff'].median():.6f}
    
    Geographic Coverage:
      Longitude: {df['center_lon'].min():.2f} to {df['center_lon'].max():.2f}
      Latitude: {df['center_lat'].min():.2f} to {df['center_lat'].max():.2f}
    
    Watershed Complexity:
      Avg Coordinates per Watershed: {df['coord_count'].mean():.0f}
      Max Coordinates: {df['coord_count'].max():,}
    """
    
    ax6.text(0.1, 0.5, summary_text, fontsize=12, verticalalignment='center',
             bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8))
    
    plt.suptitle('USGS Gage Data Analysis Dashboard', fontsize=16, y=0.98)
    plt.savefig('data/Outputs/summary_dashboard.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """Main visualization function"""
    print("Loading gage data...")
    df = load_gage_data()
    print(f"Loaded {len(df)} gage records")
    
    # Create output directory
    Path("data/Outputs").mkdir(exist_ok=True)
    
    print("\nCreating visualizations...")
    
    # Individual plots
    print("1. Gage locations map...")
    plot_gage_locations(df)
    
    print("2. Drainage area distribution...")
    plot_drainage_area_distribution(df)
    
    print("3. Quality metrics...")
    plot_quality_metrics(df)
    
    print("4. Geographic coverage...")
    plot_geographic_coverage(df)
    
    print("5. Summary dashboard...")
    create_summary_dashboard(df)
    
    print("\nAll visualizations saved to data/Outputs/")
    print("Files created:")
    print("- gage_locations.png")
    print("- drainage_area_distribution.png") 
    print("- quality_metrics.png")
    print("- geographic_coverage.png")
    print("- summary_dashboard.png")

if __name__ == "__main__":
    main()
