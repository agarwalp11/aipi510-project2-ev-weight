"""Prepare EPA FuelEconomy.gov EV records for AIPI 510 simulation."""
import pandas as pd

INPUT = 'data/vehicles.csv'
OUTPUT = 'data/ev_cleaned.csv'

# The supplied EPA export contains a standalone 'vehicles' line before the header.
df = pd.read_csv(INPUT, skiprows=1, low_memory=False)
print(f'Original records: {len(df):,}')

# Pure battery electric only; do not include plug-in hybrids.
ev = df.loc[(df['fuelType'] == 'Electricity') & df['year'].between(2020, 2025),
            ['id', 'year', 'make', 'model', 'drive', 'trany', 'VClass', 'combE', 'range']].copy()
ev = ev.rename(columns={'id': 'epa_id', 'year': 'model_year', 'combE': 'kwh_per_100_miles',
                        'range': 'range_miles', 'VClass': 'vehicle_class', 'trany': 'transmission'})
print(f'Battery-electric records (2020–2025): {len(ev):,}')
print('Missing values before filtering:\n', ev.isna().sum().to_string())
print(f'Duplicate EPA IDs: {ev.duplicated(subset=["epa_id"]).sum():,}')

# Energy is required for the response variable; other descriptive fields can remain missing.
ev = ev.dropna(subset=['epa_id', 'model_year', 'kwh_per_100_miles'])
ev = ev[ev['kwh_per_100_miles'] > 0].drop_duplicates(subset=['epa_id'])
ev['wh_per_km'] = ev['kwh_per_100_miles'] * 1000 / (100 * 1.609344)
ev = ev.sort_values(['model_year', 'make', 'model', 'epa_id']).reset_index(drop=True)
ev.to_csv(OUTPUT, index=False)
print(f'Final records: {len(ev):,}')
print(f'Saved {OUTPUT}')
print(ev.head(5).to_string(index=False))
