import pandas as pd

# Load cleaned EPA data
df = pd.read_csv('data/ev_cleaned.csv')

# Examine the dataset
print(df.info())
print(df.describe())

# Compare average consumption by drivetrain
print(
    df.groupby('drive')['wh_per_km']
    .agg(['count', 'mean', 'std'])
    .round(2)
)

# Compare average consumption by vehicle class
print(
    df.groupby('vehicle_class')['wh_per_km']
    .agg(['count', 'mean', 'std'])
    .round(2)
)

# Estimate the additional energy from 200 kg
added_mass = 200
gravity = 9.81
rolling_coeff = 0.010
efficiency = 0.90

delta_energy = (
    rolling_coeff * added_mass * gravity
) / (3.6 * efficiency)

df['loaded_wh_km'] = df['wh_per_km'] + delta_energy

df['percent_increase'] = (
    (df['loaded_wh_km'] - df['wh_per_km'])
    / df['wh_per_km']
) * 100

print(
    df[['make', 'model', 'wh_per_km',
        'loaded_wh_km', 'percent_increase']].head(10)
)