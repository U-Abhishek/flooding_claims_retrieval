import os
import scipy.io
import numpy as np
import pandas as pd

def extract_gage_info(mat_path, var_name):
    mat = scipy.io.loadmat(mat_path)
    gages = mat.get(var_name)
    events = []
    if gages is not None:
        for entry in gages:
            # Each entry is a tuple with known structure
            tup = entry[0]
            # Extract gauge id, coordinates, discharge, sqmi
            try:
                gauge_id = tup[4][0] if len(tup[4]) > 0 else None
                lon = tup[1][:,0].tolist() if tup[1].ndim == 2 else tup[1].tolist()
                lat = tup[1][:,1].tolist() if tup[1].ndim == 2 else tup[1].tolist()
                discharge = tup[5][0][0] if tup[5].size > 0 else None
                sqmi = tup[6][0][0] if len(tup) > 6 and tup[6].size > 0 else None
                events.append({
                    'gauge_id': gauge_id,
                    'longitude': lon,
                    'latitude': lat,
                    'discharge': discharge,
                    'sqmi': sqmi
                })
            except Exception as e:
                continue
    return events

def main():
    # Extract info from Q100Gages and keptGages
    gage_files = [
        ('data/Outputs/Q100Gages.mat', 'Q100Gages'),
        ('data/Outputs/keptGages.mat', 'keptGages')
    ]
    all_events = []
    for mat_path, var_name in gage_files:
        events = extract_gage_info(mat_path, var_name)
        all_events.extend(events)
    # Save to CSV
    df = pd.DataFrame(all_events)
    df.to_csv('data/Outputs/gage_events_summary.csv', index=False)
    print('Summary file generated: data/Outputs/gage_events_summary.csv')

if __name__ == '__main__':
    main()
