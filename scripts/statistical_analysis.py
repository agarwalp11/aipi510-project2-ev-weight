
from pathlib import Path

import os

import matplotlib



matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parents[1]

os.chdir(ROOT)


import pandas as pd

# Load the simulated experiment dataset
df = pd.read_csv("data/ev_experiment.csv")

# Verify sample sizes
print(df.groupby("vehicle_group").size())
print(f"\nTotal sample size: {len(df)}")


import numpy as np
import pandas as pd
from statsmodels.stats.power import FTestAnovaPower

# Power analysis assumptions
alpha = 0.05
target_power = 0.80
num_groups = 3

# Cohen's conventional effect sizes for ANOVA
effect_sizes = {
    "Small": 0.10,
    "Medium": 0.25,
    "Large": 0.40
}

# Initialize power analysis
power_analysis = FTestAnovaPower()

results = []

for label, effect_size in effect_sizes.items():

    # Calculate required total sample size
    required_n = power_analysis.solve_power(
        effect_size=effect_size,
        alpha=alpha,
        power=target_power,
        k_groups=num_groups
    )

    # Round up to a multiple of 3 for equal groups
    total_n = int(np.ceil(required_n / num_groups) * num_groups)

    results.append({
        "Effect Size": label,
        "Cohen's f": effect_size,
        "Total Sample Size": total_n,
        "Per Group": total_n // num_groups
    })

power_results = pd.DataFrame(results)

print(power_results.to_string(index=False))


# Randomly select one record per make/model combination
unique_df = (
    df.sample(frac=1, random_state=42)
    .drop_duplicates(
        subset=["vehicle_group", "make", "model"]
    )
)

# Randomly select 60 unique models from each group
final_df = (
    unique_df.groupby("vehicle_group", group_keys=False)
    .sample(n=60, random_state=42)
    .sort_values(["vehicle_group", "make", "model"])
    .reset_index(drop=True)
)

# Verify sample sizes
print("Final sample sizes:")
print(final_df.groupby("vehicle_group").size())

# Check for repeated models
duplicates = final_df.duplicated(
    subset=["make", "model"]
).sum()

print(f"\nRepeated models: {duplicates}")
print(f"Total sample size: {len(final_df)}")

# Save final dataset
final_df.to_csv("data/ev_final_sample.csv", index=False)


from scipy.stats import shapiro, levene

groups = ["Passenger Cars", "SUVs", "Pickup Trucks"]

group_data = [
    final_df.loc[
        final_df["vehicle_group"] == group,
        "percent_increase"
    ].values
    for group in groups
]

# Normality tests
print("Shapiro-Wilk normality tests:")

for group, values in zip(groups, group_data):
    stat, p = shapiro(values)
    print(f"{group}: W={stat:.4f}, p={p:.4f}")

# Equal variance test
stat, p = levene(*group_data, center="median")

print(f"\nLevene's test: statistic={stat:.4f}, p={p:.4f}")


from statsmodels.stats.oneway import anova_oneway

# Welch's ANOVA
welch_result = anova_oneway(
    data=final_df["percent_increase"],
    groups=final_df["vehicle_group"],
    use_var="unequal"
)

print(welch_result)


from scipy.stats import studentized_range
import numpy as np
import pandas as pd

# Group summary statistics
summary = final_df.groupby("vehicle_group")["percent_increase"].agg(
    ["mean", "var", "count"]
)

groups = summary.index.tolist()
k = len(groups)
results = []

for i in range(k):
    for j in range(i + 1, k):
        group1 = groups[i]
        group2 = groups[j]

        mean_diff = summary.loc[group1, "mean"] - summary.loc[group2, "mean"]

        v1 = summary.loc[group1, "var"] / summary.loc[group1, "count"]
        v2 = summary.loc[group2, "var"] / summary.loc[group2, "count"]

        se = np.sqrt(v1 + v2)

        # Welch-Satterthwaite degrees of freedom
        df_welch = (v1 + v2)**2 / (
            v1**2 / (summary.loc[group1, "count"] - 1)
            + v2**2 / (summary.loc[group2, "count"] - 1)
        )

        # Games-Howell statistic and adjusted p-value
        q = np.sqrt(2) * abs(mean_diff) / se
        p_adjusted = studentized_range.sf(q, k, df_welch)

        results.append({
            "Group 1": group1,
            "Group 2": group2,
            "Mean Difference": mean_diff,
            "Adjusted p-value": p_adjusted
        })

games_howell_results = pd.DataFrame(results)

print(games_howell_results.to_string(index=False))


# Calculate observed eta-squared

grand_mean = final_df["percent_increase"].mean()

group_stats = final_df.groupby("vehicle_group")[
    "percent_increase"
].agg(["mean", "count"])

# Variation explained by differences between groups
ss_between = (
    group_stats["count"] *
    (group_stats["mean"] - grand_mean) ** 2
).sum()

# Total variation in the dataset
ss_total = (
    (final_df["percent_increase"] - grand_mean) ** 2
).sum()

# Eta-squared
eta_squared = ss_between / ss_total

print(f"Observed eta-squared: {eta_squared:.4f}")
print(f"Percentage of variation associated with vehicle class: {eta_squared * 100:.2f}%")


import numpy as np
import pandas as pd
from scipy.stats import t

# Calculate group summary statistics
ci_results = (
    final_df.groupby("vehicle_group")["percent_increase"]
    .agg(["count", "mean", "std"])
    .reset_index()
)

# Standard error of each group mean
ci_results["se"] = (
    ci_results["std"] / np.sqrt(ci_results["count"])
)

# Critical t-value for 95% confidence intervals
ci_results["t_critical"] = t.ppf(
    0.975,
    df=ci_results["count"] - 1
)

# Margin of error
ci_results["margin_error"] = (
    ci_results["t_critical"] * ci_results["se"]
)

# Confidence interval bounds
ci_results["ci_lower"] = (
    ci_results["mean"] - ci_results["margin_error"]
)

ci_results["ci_upper"] = (
    ci_results["mean"] + ci_results["margin_error"]
)

print(
    ci_results[
        ["vehicle_group", "count", "mean",
        "ci_lower", "ci_upper"]
    ].round(3)
)


import matplotlib.pyplot as plt

# Set the order of the vehicle groups
order = ["Passenger Cars", "SUVs", "Pickup Trucks"]

plot_df = (
    ci_results.set_index("vehicle_group")
    .loc[order]
)

# Create chart
fig, ax = plt.subplots(figsize=(9, 5))

bars = ax.bar(
    plot_df.index,
    plot_df["mean"],
    yerr=plot_df["margin_error"],
    capsize=6,
    color=["#4472C4", "#70AD47", "#ED7D31"],
    edgecolor="black",
    alpha=0.85
)

# Add mean labels
for bar, mean in zip(bars, plot_df["mean"]):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.15,
        f"{mean:.2f}%",
        ha="center",
        fontsize=11
    )

ax.set_title(
    "Modeled Impact of Adding 200 kg to Electric Vehicles",
    fontsize=14,
    fontweight="bold"
)

ax.set_ylabel("Mean Energy Consumption Increase (%)")
ax.set_xlabel("Vehicle Class")
ax.set_ylim(0, 3.5)

ax.grid(axis="y", alpha=0.2)
ax.set_axisbelow(True)

plt.tight_layout()

# Save figure for report and presentation
plt.savefig(
    "ev_weight_results.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close(fig)


import numpy as np

# Simulation assumptions
added_mass = 200
crr = 0.01
gravity = 9.81
efficiency = 0.90

# Expected additional energy consumption
expected_increase = (
    crr * added_mass * gravity / (3.6 * efficiency)
)

print(f"Expected increase: {expected_increase:.4f} Wh/km")

# Verify simulated values
actual_increase = (
    final_df["loaded_wh_km"] - final_df["wh_per_km"]
)

print(
    "Actual mean increase:",
    round(actual_increase.mean(), 4),
    "Wh/km"
)

print(
    "All increases match model:",
    np.allclose(actual_increase, expected_increase)
)

# Verify percentage increase formula
expected_percent = (
    actual_increase / final_df["wh_per_km"] * 100
)

print(
    "Percentage calculations correct:",
    np.allclose(
        final_df["percent_increase"],
        expected_percent
    )
)


# Verify final sample
print("Total observations:", len(final_df))

print("\nObservations per group:")
print(final_df.groupby("vehicle_group").size())

print("\nRepeated make/model combinations:")
print(
    final_df.duplicated(
        subset=["make", "model"]
    ).sum()
)

print("\nMissing percentage values:")
print(final_df["percent_increase"].isna().sum())
