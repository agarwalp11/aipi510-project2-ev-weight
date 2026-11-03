import pandas as pd

# Load EPA data
df = pd.read_csv("data/ev_cleaned.csv")

# Assign broad vehicle categories
def classify_vehicle(vehicle_class):
    if "Pickup Trucks" in vehicle_class:
        return "Pickup Trucks"
    elif "Sport Utility Vehicle" in vehicle_class:
        return "SUVs"
    elif "Cars" in vehicle_class or "Station Wagons" in vehicle_class:
        return "Passenger Cars"
    else:
        return None

df["vehicle_group"] = df["vehicle_class"].apply(classify_vehicle)

# Remove vehicles outside our three groups
df = df.dropna(subset=["vehicle_group"]).copy()

# Simulation parameters
added_mass = 200
gravity = 9.81
rolling_coeff = 0.010
efficiency = 0.90

# Additional energy consumption (Wh/km)
delta_energy = (
    rolling_coeff * added_mass * gravity
) / (3.6 * efficiency)

# Simulate loaded energy consumption
df["loaded_wh_km"] = df["wh_per_km"] + delta_energy

# Calculate percentage increase
df["percent_increase"] = (
    (df["loaded_wh_km"] - df["wh_per_km"])
    / df["wh_per_km"]
) * 100

# Save experiment dataset
df.to_csv("data/ev_experiment.csv", index=False)

# Display group statistics
print(df.groupby("vehicle_group")["percent_increase"].agg(
    ["count", "mean", "std"]
).round(3))

print(f"\nTotal vehicles: {len(df)}")