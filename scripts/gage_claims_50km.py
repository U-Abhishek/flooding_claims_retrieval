import pandas as pd
import numpy as np
from sklearn.neighbors import BallTree

def parse_coord(coord):
    if isinstance(coord, str):
        try:
            vals = eval(coord)
            return [float(v) for v in vals]
        except:
            return []
    elif isinstance(coord, (list, tuple, np.ndarray)):
        return [float(v) for v in coord]
    return []

def main():
    claims = pd.read_csv('data/Outputs/goodClaims.csv', delimiter=';', low_memory=False)
    gages = pd.read_csv('data/Outputs/gage_events_summary.csv')

    claims.columns = claims.columns.str.strip()
    gages.columns = gages.columns.str.strip()

    claims = claims.dropna(subset=['longitude', 'latitude', 'dateOfLoss'])
    claims['longitude'] = claims['longitude'].astype(float)
    claims['latitude'] = claims['latitude'].astype(float)
    claims['dateOfLoss'] = pd.to_datetime(claims['dateOfLoss'], errors='coerce')
    claims = claims.dropna(subset=['dateOfLoss'])

    claim_points_rad = np.radians(claims[['longitude', 'latitude']].to_numpy())
    tree = BallTree(claim_points_rad, metric='haversine')
    radius = 50 / 6371.0  # 50km in radians

    output_rows = []
    for _, gage in gages.iterrows():
        lon_arr = parse_coord(gage['longitude'])
        lat_arr = parse_coord(gage['latitude'])
        gage_dates = []
        gage_counts = []
        for lon_g, lat_g in zip(lon_arr, lat_arr):
            gage_point_rad = np.radians([[lon_g, lat_g]])
            ind = tree.query_radius(gage_point_rad, r=radius)[0]
            if len(ind) > 0:
                matched_claims = claims.iloc[ind]
                date_counts = matched_claims.groupby('dateOfLoss').size()
                gage_dates.extend(date_counts.index.strftime('%Y-%m-%d').tolist())
                gage_counts.extend(date_counts.values.tolist())
        row = gage.to_dict()
        row['dates'] = gage_dates
        row['num_claims'] = gage_counts
        output_rows.append(row)
    output_df = pd.DataFrame(output_rows)
    output_df.to_csv('data/Outputs/gage_claims_50km.csv', index=False)
    print('Output written to data/Outputs/gage_claims_50km.csv')

if __name__ == '__main__':
    main()
