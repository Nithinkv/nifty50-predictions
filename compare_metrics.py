import pandas as pd
import os

# Load both metrics files
metrics_50 = pd.read_csv("output/metrics_short_50.csv")
metrics_expanded = pd.read_csv("output/metrics_short.csv")

# Create comparison dataframe
comparison = pd.DataFrame({
    "Metric": ["Annual Return", "Annual Volatility", "Sharpe Ratio", "Total Return (%)"],
    "Original 50": [
        f"{metrics_50['ann_return'].iloc[0]:.4f}",
        f"{metrics_50['ann_vol'].iloc[0]:.4f}",
        f"{metrics_50['sharpe'].iloc[0]:.4f}",
        f"{metrics_50['total_return'].iloc[0]:.2f}%"
    ],
    "Expanded (86)": [
        f"{metrics_expanded['ann_return'].iloc[0]:.4f}",
        f"{metrics_expanded['ann_vol'].iloc[0]:.4f}",
        f"{metrics_expanded['sharpe'].iloc[0]:.4f}",
        f"{metrics_expanded['total_return'].iloc[0]:.2f}%"
    ]
})

print("\n" + "="*70)
print("MODEL PERFORMANCE COMPARISON: Original 50 vs Expanded Universe (86)")
print("="*70)
print(comparison.to_string(index=False))
print("="*70)

# Calculate differences
print("\nDifference (Expanded - Original 50):")
print(f"  Annual Return:      {metrics_expanded['ann_return'].iloc[0] - metrics_50['ann_return'].iloc[0]:+.4f}")
print(f"  Annual Volatility:  {metrics_expanded['ann_vol'].iloc[0] - metrics_50['ann_vol'].iloc[0]:+.4f}")
print(f"  Sharpe Ratio:       {metrics_expanded['sharpe'].iloc[0] - metrics_50['sharpe'].iloc[0]:+.4f}")
print(f"  Total Return:       {metrics_expanded['total_return'].iloc[0] - metrics_50['total_return'].iloc[0]:+.2f}%")

# Save comparison to CSV
comparison.to_csv("output/metrics_comparison.csv", index=False)
print("\n✓ Comparison saved to: output/metrics_comparison.csv")
