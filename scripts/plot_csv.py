import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import ast

def load_csv_data():
    """Load gage data from CSV file"""
    csv_file = "data/Outputs/gage_events_summary.csv"
    df = pd.read_csv(csv_file)
    
    print(f"Loaded {len(df)} records from CSV")
    print(f"Columns: {list(df.columns)}")
    print(f"Sample data:")
    print(df.head())
    
    return df

def parse_coordinates(df):
    """Parse the coordinate strings into separate lat/lon values"""
    # Parse longitude and latitude from string format
    df['lon_min'] = df['longitude'].apply(lambda x: ast.literal_eval(x)[0])
    df['lon_max'] = df['longitude'].apply(lambda x: ast.literal_eval(x)[1])
    df['lat_min'] = df['latitude'].apply(lambda x: ast.literal_eval(x)[0])
    df['lat_max'] = df['latitude'].apply(lambda x: ast.literal_eval(x)[1])
    
    # Calculate center coordinates
    df['center_lon'] = (df['lon_min'] + df['lon_max']) / 2
    df['center_lat'] = (df['lat_min'] + df['lat_max']) / 2
    
    return df

def create_gage_map(df):
    """Create a map showing gage locations and discharge data"""
    
    # Parse coordinates
    df = parse_coordinates(df)
    
    print(f"Creating map with {len(df)} gage records")
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # Plot gage locations with size based on drainage area and color based on discharge
    scatter = ax.scatter(df['center_lon'], df['center_lat'], 
                        s=df['sqmi'] * 0.5,        # Size based on drainage area (sq mi)
                        c=df['discharge'],         # Color based on discharge
                        alpha=0.7, 
                        cmap='viridis',
                        edgecolors='black',
                        linewidth=0.5)
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
    cbar.set_label('Discharge (cfs)', fontsize=12)
    
    # Set labels and title
    ax.set_xlabel('Longitude', fontsize=14)
    ax.set_ylabel('Latitude', fontsize=14)
    ax.set_title(f'USGS Gage Locations and Discharge Data\n'
                f'Size = Drainage Area (sq mi), Color = Discharge (cfs)\n'
                f'Total Gages: {len(df):,}', fontsize=16)
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    # Add statistics as text
    stats_text = f"""Statistics:
• Discharge Range: {df['discharge'].min():.1f} - {df['discharge'].max():.1f} cfs
• Drainage Area Range: {df['sqmi'].min():.1f} - {df['sqmi'].max():.1f} sq mi
• Geographic Coverage:
  Longitude: {df['center_lon'].min():.2f}° to {df['center_lon'].max():.2f}°
  Latitude: {df['center_lat'].min():.2f}° to {df['center_lat'].max():.2f}°
• Mean Discharge: {df['discharge'].mean():.1f} cfs
• Mean Drainage Area: {df['sqmi'].mean():.1f} sq mi"""
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=dict(boxstyle="round,pad=0.5", 
            facecolor="white", alpha=0.8))
    
    # Add legend for size
    drainage_areas = [100, 1000, 5000, 10000]  # Example drainage areas
    labels = [f'{area} sq mi' for area in drainage_areas]
    legend_elements = [plt.scatter([], [], s=area*0.5, c='gray', alpha=0.7, 
                                 edgecolors='black', linewidth=0.5, label=label) 
                      for area, label in zip(drainage_areas, labels)]
    
    ax.legend(handles=legend_elements, title='Drainage Area', 
             loc='lower right', fontsize=10)
    
    plt.tight_layout()
    
    # Save the plot
    output_file = "data/Outputs/gage_discharge_map.png"
    Path("data/Outputs").mkdir(exist_ok=True)
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Map saved to {output_file}")
    
    plt.show()

def create_discharge_histogram(df):
    """Create histogram of discharge values"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Linear scale histogram
    ax1.hist(df['discharge'], bins=50, alpha=0.7, color='skyblue', edgecolor='black')
    ax1.set_xlabel('Discharge (cfs)')
    ax1.set_ylabel('Number of Gages')
    ax1.set_title('Distribution of Discharge Values')
    ax1.grid(True, alpha=0.3)
    
    # Log scale histogram
    ax2.hist(np.log10(df['discharge']), bins=50, alpha=0.7, color='lightcoral', edgecolor='black')
    ax2.set_xlabel('Log10(Discharge)')
    ax2.set_ylabel('Number of Gages')
    ax2.set_title('Distribution of Discharge Values (Log Scale)')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('data/Outputs/discharge_distribution.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """Main function"""
    print("Loading CSV data...")
    df = load_csv_data()
    
    print("Creating gage map...")
    create_gage_map(df)
    
    print("Creating discharge histogram...")
    create_discharge_histogram(df)

if __name__ == "__main__":
    main()
