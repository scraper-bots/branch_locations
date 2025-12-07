#!/usr/bin/env python3
"""
Bank Branch Network Analysis Script
Generates all charts and analysis for Bank of Baku
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial import distance_matrix
from sklearn.cluster import KMeans, DBSCAN
from sklearn.neighbors import NearestNeighbors
from scipy.stats import gaussian_kde
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Set figure defaults
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

print("=" * 80)
print("BANK BRANCH NETWORK ANALYSIS")
print("Focus: Strategic Insights for Bank of Baku")
print("=" * 80)
print()

# Load data
print("Loading data...")
df = pd.read_csv('data/combined_atms.csv')

# Convert coordinates to numeric
df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
df['long'] = pd.to_numeric(df['long'], errors='coerce')

# Remove any rows with invalid coordinates
df = df.dropna(subset=['lat', 'long'])

print(f"Total branches loaded: {len(df)}")
print(f"Banks in dataset: {df['bank_name'].nunique()}")
print()

# ============================================================================
# Chart 1: Branch count by bank
# ============================================================================
print("Generating Chart 1: Branch Count Comparison...")
fig, ax = plt.subplots(figsize=(14, 7))

branch_counts = df['bank_name'].value_counts().sort_values(ascending=True)
colors = ['#e74c3c' if bank == 'Bank of Baku' else '#3498db' for bank in branch_counts.index]

branch_counts.plot(kind='barh', ax=ax, color=colors)
ax.set_xlabel('Number of Branches', fontsize=12, fontweight='bold')
ax.set_ylabel('Bank Name', fontsize=12, fontweight='bold')
ax.set_title('Branch Network Size Comparison - Bank of Baku vs Competitors',
             fontsize=14, fontweight='bold', pad=20)

# Add value labels
for i, v in enumerate(branch_counts.values):
    ax.text(v + 2, i, str(v), va='center', fontweight='bold')

plt.tight_layout()
plt.savefig('charts/01_branch_count_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# Key insight
bob_count = df[df['bank_name'] == 'Bank of Baku'].shape[0]
total_count = len(df)
bob_rank = (df['bank_name'].value_counts() > bob_count).sum() + 1

print(f"✓ Chart 1 saved")
print(f"  Bank of Baku: {bob_count} branches, Rank #{bob_rank}, Market share: {bob_count/total_count*100:.1f}%")
print()

# ============================================================================
# Chart 2: Market share pie chart
# ============================================================================
print("Generating Chart 2: Market Share Analysis...")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

# Overall market share
market_share = df['bank_name'].value_counts()
colors_pie = ['#e74c3c' if bank == 'Bank of Baku' else '#ecf0f1' for bank in market_share.index]
explode = [0.1 if bank == 'Bank of Baku' else 0 for bank in market_share.index]

ax1.pie(market_share.values, labels=market_share.index, autopct='%1.1f%%',
        colors=colors_pie, explode=explode, startangle=90)
ax1.set_title('Overall Market Share by Branch Count', fontsize=14, fontweight='bold')

# Top 5 vs Bank of Baku
top_5 = market_share.head(5)
if 'Bank of Baku' not in top_5.index:
    top_5_list = list(top_5.index[:4]) + ['Bank of Baku']
    top_5 = market_share[top_5_list]

colors_bar = ['#e74c3c' if bank == 'Bank of Baku' else '#3498db' for bank in top_5.index]
top_5.plot(kind='bar', ax=ax2, color=colors_bar)
ax2.set_title('Top Banks by Branch Count', fontsize=14, fontweight='bold')
ax2.set_xlabel('Bank', fontsize=11)
ax2.set_ylabel('Number of Branches', fontsize=11)
ax2.tick_params(axis='x', rotation=45)

# Add value labels
for i, v in enumerate(top_5.values):
    ax2.text(i, v + 2, str(v), ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig('charts/02_market_share_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"✓ Chart 2 saved")
print()

# ============================================================================
# Chart 3: Geographic scatter plot
# ============================================================================
print("Generating Chart 3: Geographic Distribution...")
fig, ax = plt.subplots(figsize=(14, 10))

# Plot all banks
for bank in df['bank_name'].unique():
    bank_data = df[df['bank_name'] == bank]
    if bank == 'Bank of Baku':
        ax.scatter(bank_data['long'], bank_data['lat'],
                  s=150, alpha=0.8, label=bank,
                  edgecolors='black', linewidth=2, marker='s', zorder=5)
    else:
        ax.scatter(bank_data['long'], bank_data['lat'],
                  s=50, alpha=0.5, label=bank)

ax.set_xlabel('Longitude', fontsize=12, fontweight='bold')
ax.set_ylabel('Latitude', fontsize=12, fontweight='bold')
ax.set_title('Geographic Distribution of Bank Branches in Azerbaijan\\n(Bank of Baku highlighted in squares)',
             fontsize=14, fontweight='bold', pad=20)
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('charts/03_geographic_distribution_all.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"✓ Chart 3 saved")
print()

# ============================================================================
# Chart 4: Bank of Baku vs top 3 competitors
# ============================================================================
print("Generating Chart 4: Bank of Baku vs Top Competitors...")
top_3_competitors = df['bank_name'].value_counts().head(3).index.tolist()
comparison_banks = ['Bank of Baku'] + [b for b in top_3_competitors if b != 'Bank of Baku'][:3]

fig, axes = plt.subplots(2, 2, figsize=(16, 14))
axes = axes.flatten()

for idx, bank in enumerate(comparison_banks):
    ax = axes[idx]

    # Plot all branches in gray
    ax.scatter(df['long'], df['lat'], s=20, alpha=0.2, color='gray', label='Other banks')

    # Highlight this bank
    bank_data = df[df['bank_name'] == bank]
    color = '#e74c3c' if bank == 'Bank of Baku' else '#3498db'
    ax.scatter(bank_data['long'], bank_data['lat'],
              s=100, alpha=0.8, color=color, label=bank,
              edgecolors='black', linewidth=1, zorder=5)

    ax.set_title(f'{bank} - {len(bank_data)} branches',
                fontsize=12, fontweight='bold')
    ax.set_xlabel('Longitude', fontsize=10)
    ax.set_ylabel('Latitude', fontsize=10)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

plt.suptitle('Geographic Coverage Comparison: Bank of Baku vs Top Competitors',
             fontsize=16, fontweight='bold', y=1.00)
plt.tight_layout()
plt.savefig('charts/04_bob_vs_competitors_geographic.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"✓ Chart 4 saved")
print()

# ============================================================================
# Chart 5: Regional Clustering Analysis
# ============================================================================
print("Generating Chart 5: Regional Clustering...")
coords = df[['lat', 'long']].values
clustering = DBSCAN(eps=0.5, min_samples=5).fit(coords)
df['cluster'] = clustering.labels_

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))

# All banks clusters
scatter1 = ax1.scatter(df['long'], df['lat'], c=df['cluster'],
                       cmap='tab20', s=50, alpha=0.6)
ax1.set_title('Regional Clusters - All Banks', fontsize=14, fontweight='bold')
ax1.set_xlabel('Longitude', fontsize=11)
ax1.set_ylabel('Latitude', fontsize=11)
ax1.grid(True, alpha=0.3)
plt.colorbar(scatter1, ax=ax1, label='Cluster ID')

# Bank of Baku presence in clusters
bob_clusters = df[df['bank_name'] == 'Bank of Baku']['cluster'].value_counts().sort_index()
all_clusters = df['cluster'].value_counts().sort_index()

cluster_df = pd.DataFrame({
    'Total Branches': all_clusters,
    'Bank of Baku': bob_clusters
}).fillna(0)

cluster_df.plot(kind='bar', ax=ax2, color=['#3498db', '#e74c3c'])
ax2.set_title('Bank of Baku Presence by Regional Cluster', fontsize=14, fontweight='bold')
ax2.set_xlabel('Cluster ID (-1 = outliers)', fontsize=11)
ax2.set_ylabel('Number of Branches', fontsize=11)
ax2.legend(fontsize=10)
ax2.tick_params(axis='x', rotation=0)

plt.tight_layout()
plt.savefig('charts/05_regional_clustering.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"✓ Chart 5 saved")
print(f"  Identified {df['cluster'].nunique() - 1} major regional clusters")
print()

# ============================================================================
# Chart 6: Baku city analysis
# ============================================================================
print("Generating Chart 6: Baku City Analysis...")
baku_df = df[(df['lat'] >= 40.3) & (df['lat'] <= 40.5) &
             (df['long'] >= 49.7) & (df['long'] <= 50.0)].copy()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))

# Baku branch distribution
for bank in baku_df['bank_name'].unique():
    bank_data = baku_df[baku_df['bank_name'] == bank]
    if bank == 'Bank of Baku':
        ax1.scatter(bank_data['long'], bank_data['lat'],
                   s=150, alpha=0.8, label=bank,
                   edgecolors='black', linewidth=2, marker='s', zorder=5)
    else:
        ax1.scatter(bank_data['long'], bank_data['lat'],
                   s=50, alpha=0.5, label=bank)

ax1.set_xlabel('Longitude', fontsize=11)
ax1.set_ylabel('Latitude', fontsize=11)
ax1.set_title('Baku City - Branch Distribution', fontsize=14, fontweight='bold')
ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
ax1.grid(True, alpha=0.3)

# Baku market share
baku_counts = baku_df['bank_name'].value_counts()
colors = ['#e74c3c' if bank == 'Bank of Baku' else '#3498db' for bank in baku_counts.index]
baku_counts.plot(kind='barh', ax=ax2, color=colors)
ax2.set_xlabel('Number of Branches', fontsize=11)
ax2.set_ylabel('Bank Name', fontsize=11)
ax2.set_title('Baku City - Branch Count by Bank', fontsize=14, fontweight='bold')

for i, v in enumerate(baku_counts.values):
    ax2.text(v + 0.5, i, str(v), va='center', fontweight='bold')

plt.tight_layout()
plt.savefig('charts/06_baku_city_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

bob_baku = len(baku_df[baku_df['bank_name'] == 'Bank of Baku'])
total_baku = len(baku_df)

print(f"✓ Chart 6 saved")
print(f"  Baku: {bob_baku} Bank of Baku branches out of {total_baku} total ({bob_baku/total_baku*100:.1f}%)")
print()

# ============================================================================
# Chart 7: Baku vs Regions comparison
# ============================================================================
print("Generating Chart 7: Baku vs Regions...")
df['region'] = df.apply(lambda row: 'Baku' if (40.3 <= row['lat'] <= 40.5 and 49.7 <= row['long'] <= 50.0) else 'Regions', axis=1)

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Regional distribution for all banks
region_dist = df.groupby(['bank_name', 'region']).size().unstack(fill_value=0)
region_dist.plot(kind='bar', ax=axes[0], color=['#3498db', '#e74c3c'], width=0.8)
axes[0].set_title('Baku vs Regions - All Banks', fontsize=12, fontweight='bold')
axes[0].set_xlabel('Bank', fontsize=10)
axes[0].set_ylabel('Number of Branches', fontsize=10)
axes[0].tick_params(axis='x', rotation=45)
axes[0].legend(title='Region')

# Bank of Baku specific
bob_region = df[df['bank_name'] == 'Bank of Baku']['region'].value_counts()
bob_region.plot(kind='pie', ax=axes[1], autopct='%1.1f%%',
                colors=['#3498db', '#e74c3c'], startangle=90)
axes[1].set_title('Bank of Baku: Baku vs Regions', fontsize=12, fontweight='bold')
axes[1].set_ylabel('')

# Percentage in regions
region_pct = region_dist.div(region_dist.sum(axis=1), axis=0) * 100
region_pct['Regions'].sort_values(ascending=True).plot(kind='barh', ax=axes[2], color='#2ecc71')
axes[2].set_title('Regional Coverage - % of Branches Outside Baku', fontsize=12, fontweight='bold')
axes[2].set_xlabel('Percentage (%)', fontsize=10)
axes[2].set_ylabel('Bank', fontsize=10)

for i, v in enumerate(region_pct['Regions'].sort_values(ascending=True).values):
    axes[2].text(v + 1, i, f'{v:.1f}%', va='center')

plt.tight_layout()
plt.savefig('charts/07_baku_vs_regions.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"✓ Chart 7 saved")
print()

# ============================================================================
# Chart 8: Competitive density heatmap
# ============================================================================
print("Generating Chart 8: Competitive Density...")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))

# Density for all banks
xy_all = np.vstack([df['long'], df['lat']])
z_all = gaussian_kde(xy_all)(xy_all)
scatter1 = ax1.scatter(df['long'], df['lat'], c=z_all, s=50, cmap='YlOrRd', alpha=0.6)
ax1.set_title('Branch Density Heatmap - All Banks', fontsize=14, fontweight='bold')
ax1.set_xlabel('Longitude', fontsize=11)
ax1.set_ylabel('Latitude', fontsize=11)
plt.colorbar(scatter1, ax=ax1, label='Density')
ax1.grid(True, alpha=0.3)

# Bank of Baku branches overlaid on competition density
competitors_df = df[df['bank_name'] != 'Bank of Baku']
xy_comp = np.vstack([competitors_df['long'], competitors_df['lat']])
z_comp = gaussian_kde(xy_comp)(xy_comp)

scatter2 = ax2.scatter(competitors_df['long'], competitors_df['lat'],
                       c=z_comp, s=30, cmap='Blues', alpha=0.4)
bob_df = df[df['bank_name'] == 'Bank of Baku']
ax2.scatter(bob_df['long'], bob_df['lat'],
           s=200, alpha=0.9, color='#e74c3c',
           edgecolors='black', linewidth=2, marker='*',
           label='Bank of Baku', zorder=5)

ax2.set_title('Bank of Baku Locations vs Competitor Density', fontsize=14, fontweight='bold')
ax2.set_xlabel('Longitude', fontsize=11)
ax2.set_ylabel('Latitude', fontsize=11)
plt.colorbar(scatter2, ax=ax2, label='Competitor Density')
ax2.legend(fontsize=11)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('charts/08_competitive_density.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"✓ Chart 8 saved")
print()

# ============================================================================
# Chart 9: Gap Analysis - Underserved Areas
# ============================================================================
print("Generating Chart 9: Gap Analysis...")
bob_coords = df[df['bank_name'] == 'Bank of Baku'][['lat', 'long']].values
comp_coords = df[df['bank_name'] != 'Bank of Baku'][['lat', 'long']].values
comp_banks = df[df['bank_name'] != 'Bank of Baku']['bank_name'].values

# Calculate distance to nearest Bank of Baku branch
nbrs = NearestNeighbors(n_neighbors=1).fit(bob_coords)
distances, indices = nbrs.kneighbors(comp_coords)

# Create dataframe of competitor locations with their distance to nearest BoB
gap_df = pd.DataFrame({
    'lat': comp_coords[:, 0],
    'long': comp_coords[:, 1],
    'bank': comp_banks,
    'distance_to_bob': distances.flatten()
})

# Find significant gaps (> 0.3 degrees, roughly 30km)
gaps = gap_df[gap_df['distance_to_bob'] > 0.3].sort_values('distance_to_bob', ascending=False)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))

# Map of gaps
ax1.scatter(df['long'], df['lat'], s=20, alpha=0.2, color='gray', label='All branches')
ax1.scatter(bob_coords[:, 1], bob_coords[:, 0],
           s=100, alpha=0.8, color='#e74c3c',
           edgecolors='black', linewidth=1, marker='s', label='Bank of Baku', zorder=5)
ax1.scatter(gaps['long'], gaps['lat'],
           s=gaps['distance_to_bob']*200, alpha=0.6, color='#f39c12',
           edgecolors='black', linewidth=1, label='Gap opportunities', zorder=3)

ax1.set_xlabel('Longitude', fontsize=11)
ax1.set_ylabel('Latitude', fontsize=11)
ax1.set_title('Market Gaps - Competitor Locations Far from Bank of Baku\\n(Larger circles = greater distance)',
             fontsize=13, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)

# Top gap opportunities
top_gaps = gaps.head(15)
ax2.scatter(range(len(top_gaps)), top_gaps['distance_to_bob'],
           s=100, alpha=0.7, color='#f39c12', edgecolors='black', linewidth=1)
ax2.set_xlabel('Opportunity Rank', fontsize=11)
ax2.set_ylabel('Distance to Nearest Bank of Baku Branch (degrees)', fontsize=11)
ax2.set_title('Top 15 Expansion Opportunities by Distance', fontsize=13, fontweight='bold')
ax2.grid(True, alpha=0.3)

# Add horizontal line for average
ax2.axhline(y=gaps['distance_to_bob'].mean(), color='r', linestyle='--',
           label=f'Average: {gaps["distance_to_bob"].mean():.2f}°', linewidth=2)
ax2.legend(fontsize=10)

plt.tight_layout()
plt.savefig('charts/09_gap_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"✓ Chart 9 saved")
print(f"  Found {len(gaps)} expansion opportunity locations")
print()

# ============================================================================
# Chart 10: Nearest Competitor Analysis
# ============================================================================
print("Generating Chart 10: Nearest Competitor Analysis...")
nbrs_comp = NearestNeighbors(n_neighbors=1).fit(comp_coords)
dist_to_comp, idx_comp = nbrs_comp.kneighbors(bob_coords)

bob_analysis = df[df['bank_name'] == 'Bank of Baku'].copy()
bob_analysis['dist_to_competitor'] = dist_to_comp.flatten()
bob_analysis['nearest_competitor'] = [comp_banks[i] for i in idx_comp.flatten()]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))

# Distribution of distances
ax1.hist(bob_analysis['dist_to_competitor'], bins=20, color='#3498db',
        alpha=0.7, edgecolor='black', linewidth=1.2)
ax1.axvline(bob_analysis['dist_to_competitor'].mean(), color='#e74c3c',
           linestyle='--', linewidth=2, label=f'Mean: {bob_analysis["dist_to_competitor"].mean():.3f}°')
ax1.axvline(bob_analysis['dist_to_competitor'].median(), color='#2ecc71',
           linestyle='--', linewidth=2, label=f'Median: {bob_analysis["dist_to_competitor"].median():.3f}°')
ax1.set_xlabel('Distance to Nearest Competitor (degrees)', fontsize=11)
ax1.set_ylabel('Number of Bank of Baku Branches', fontsize=11)
ax1.set_title('Bank of Baku: Distance to Nearest Competitor Distribution',
             fontsize=13, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3, axis='y')

# Nearest competitor frequency
nearest_comp_counts = bob_analysis['nearest_competitor'].value_counts()
nearest_comp_counts.plot(kind='barh', ax=ax2, color='#9b59b6')
ax2.set_xlabel('Number of Times as Nearest Competitor', fontsize=11)
ax2.set_ylabel('Bank Name', fontsize=11)
ax2.set_title('Most Frequent Direct Competitors to Bank of Baku Branches',
             fontsize=13, fontweight='bold')

for i, v in enumerate(nearest_comp_counts.values):
    ax2.text(v + 0.2, i, str(v), va='center', fontweight='bold')

plt.tight_layout()
plt.savefig('charts/10_nearest_competitor_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"✓ Chart 10 saved")
print()

# ============================================================================
# Chart 11: Competitive Intensity Index
# ============================================================================
print("Generating Chart 11: Competitive Intensity...")

def calculate_competitive_intensity(bank_name, radius=0.1):
    bank_coords = df[df['bank_name'] == bank_name][['lat', 'long']].values
    all_coords = df[['lat', 'long']].values

    intensities = []
    for coord in bank_coords:
        # Calculate distances to all branches
        distances = np.sqrt(((all_coords - coord)**2).sum(axis=1))
        # Count branches within radius (excluding self)
        nearby = (distances > 0) & (distances < radius)
        intensities.append(nearby.sum())

    return intensities

# Calculate for all banks
intensity_data = {}
for bank in df['bank_name'].unique():
    intensity_data[bank] = calculate_competitive_intensity(bank)

# Create comparison dataframe
intensity_comparison = pd.DataFrame([
    {
        'Bank': bank,
        'Avg_Competitors_Nearby': np.mean(intensities),
        'Max_Competitors_Nearby': np.max(intensities),
        'Min_Competitors_Nearby': np.min(intensities)
    }
    for bank, intensities in intensity_data.items()
]).sort_values('Avg_Competitors_Nearby', ascending=False)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))

# Average competitive intensity
colors = ['#e74c3c' if bank == 'Bank of Baku' else '#3498db'
          for bank in intensity_comparison['Bank']]
ax1.barh(intensity_comparison['Bank'], intensity_comparison['Avg_Competitors_Nearby'],
        color=colors)
ax1.set_xlabel('Average Number of Competitors Within 10km', fontsize=11)
ax1.set_ylabel('Bank', fontsize=11)
ax1.set_title('Average Competitive Intensity by Bank', fontsize=13, fontweight='bold')

for i, v in enumerate(intensity_comparison['Avg_Competitors_Nearby'].values):
    ax1.text(v + 0.5, i, f'{v:.1f}', va='center', fontweight='bold')

# Bank of Baku intensity distribution
bob_intensities = intensity_data['Bank of Baku']
ax2.hist(bob_intensities, bins=15, color='#e74c3c', alpha=0.7,
        edgecolor='black', linewidth=1.2)
ax2.axvline(np.mean(bob_intensities), color='black', linestyle='--',
           linewidth=2, label=f'Mean: {np.mean(bob_intensities):.1f}')
ax2.set_xlabel('Number of Competitors Within 10km', fontsize=11)
ax2.set_ylabel('Number of Bank of Baku Branches', fontsize=11)
ax2.set_title('Bank of Baku: Competitive Intensity Distribution',
             fontsize=13, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('charts/11_competitive_intensity.png', dpi=300, bbox_inches='tight')
plt.close()

bob_avg_intensity = intensity_comparison[intensity_comparison['Bank'] == 'Bank of Baku']['Avg_Competitors_Nearby'].values[0]

print(f"✓ Chart 11 saved")
print(f"  Bank of Baku avg competitive intensity: {bob_avg_intensity:.1f} competitors within 10km")
print()

# ============================================================================
# Chart 12: Market Share by Geographic Quadrants
# ============================================================================
print("Generating Chart 12: Quadrant Analysis...")
lat_median = df['lat'].median()
long_median = df['long'].median()

def assign_quadrant(row):
    if row['lat'] >= lat_median and row['long'] >= long_median:
        return 'Northeast'
    elif row['lat'] >= lat_median and row['long'] < long_median:
        return 'Northwest'
    elif row['lat'] < lat_median and row['long'] >= long_median:
        return 'Southeast'
    else:
        return 'Southwest'

df['quadrant'] = df.apply(assign_quadrant, axis=1)

fig, axes = plt.subplots(2, 2, figsize=(16, 14))
axes = axes.flatten()

quadrants = ['Northeast', 'Northwest', 'Southeast', 'Southwest']

for idx, quadrant in enumerate(quadrants):
    ax = axes[idx]
    quad_data = df[df['quadrant'] == quadrant]
    quad_counts = quad_data['bank_name'].value_counts()

    colors = ['#e74c3c' if bank == 'Bank of Baku' else '#3498db' for bank in quad_counts.index]
    quad_counts.plot(kind='barh', ax=ax, color=colors)

    ax.set_title(f'{quadrant} Quadrant ({len(quad_data)} branches)',
                fontsize=12, fontweight='bold')
    ax.set_xlabel('Number of Branches', fontsize=10)
    ax.set_ylabel('Bank', fontsize=10)

    # Add value labels
    for i, v in enumerate(quad_counts.values):
        ax.text(v + 0.3, i, str(v), va='center', fontsize=9)

plt.suptitle('Market Share Analysis by Geographic Quadrants',
             fontsize=16, fontweight='bold', y=0.995)
plt.tight_layout()
plt.savefig('charts/12_quadrant_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"✓ Chart 12 saved")
print()

# ============================================================================
# Chart 13: Growth Opportunity Score
# ============================================================================
print("Generating Chart 13: Growth Opportunity Score...")

# Create grid of potential locations
lat_min, lat_max = df['lat'].min() - 0.1, df['lat'].max() + 0.1
long_min, long_max = df['long'].min() - 0.1, df['long'].max() + 0.1

# Create grid points
grid_resolution = 30
lat_grid = np.linspace(lat_min, lat_max, grid_resolution)
long_grid = np.linspace(long_min, long_max, grid_resolution)
grid_points = np.array([[lat, long] for lat in lat_grid for long in long_grid])

# Calculate opportunity score for each grid point
def calculate_opportunity_score(point):
    # Distance to nearest BoB branch (higher = better)
    distances_bob = np.sqrt(((bob_coords - point)**2).sum(axis=1))
    dist_score = distances_bob.min()

    # Number of competitors nearby (higher = more demand)
    distances_comp = np.sqrt(((comp_coords - point)**2).sum(axis=1))
    nearby_comps = (distances_comp < 0.2).sum()  # Within ~20km

    # Combined score (normalize both)
    score = dist_score * 10 + nearby_comps * 0.5
    return score

opportunity_scores = np.array([calculate_opportunity_score(point) for point in grid_points])
opportunity_scores = opportunity_scores.reshape(grid_resolution, grid_resolution)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))

# Heatmap of opportunity scores
im = ax1.contourf(long_grid, lat_grid, opportunity_scores, levels=20, cmap='YlOrRd', alpha=0.7)
ax1.scatter(bob_coords[:, 1], bob_coords[:, 0], s=100, color='blue',
           marker='s', edgecolors='black', linewidth=2, label='Bank of Baku', zorder=5)
ax1.scatter(comp_coords[:, 1], comp_coords[:, 0], s=10, color='gray',
           alpha=0.3, label='Competitors')
ax1.set_xlabel('Longitude', fontsize=11)
ax1.set_ylabel('Latitude', fontsize=11)
ax1.set_title('Expansion Opportunity Heatmap for Bank of Baku\\n(Warmer colors = higher opportunity)',
             fontsize=13, fontweight='bold')
ax1.legend(fontsize=10)
plt.colorbar(im, ax=ax1, label='Opportunity Score')

# Top opportunity locations
top_n = 20
flat_indices = opportunity_scores.flatten().argsort()[-top_n:][::-1]
top_opportunities = grid_points[flat_indices]

# Plot top opportunities
ax2.scatter(df['long'], df['lat'], s=20, alpha=0.2, color='gray', label='Existing branches')
ax2.scatter(bob_coords[:, 1], bob_coords[:, 0], s=100, color='#e74c3c',
           marker='s', edgecolors='black', linewidth=2, label='Bank of Baku', zorder=5)
ax2.scatter(top_opportunities[:, 1], top_opportunities[:, 0],
           s=200, color='#f39c12', marker='*',
           edgecolors='black', linewidth=1.5, label='Top expansion opportunities', zorder=6)

# Number the top 5
for i in range(min(5, len(top_opportunities))):
    ax2.annotate(str(i+1), (top_opportunities[i, 1], top_opportunities[i, 0]),
                fontsize=10, fontweight='bold', ha='center', va='center')

ax2.set_xlabel('Longitude', fontsize=11)
ax2.set_ylabel('Latitude', fontsize=11)
ax2.set_title(f'Top {top_n} Recommended Expansion Locations', fontsize=13, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('charts/13_growth_opportunity_score.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"✓ Chart 13 saved")
print()

# ============================================================================
# Chart 14: Multi-metric comparison with top banks
# ============================================================================
print("Generating Chart 14: Multi-Metric Comparison...")

top_5_banks = df['bank_name'].value_counts().head(5).index
if 'Bank of Baku' not in top_5_banks:
    comparison_banks = list(top_5_banks[:4]) + ['Bank of Baku']
else:
    comparison_banks = list(top_5_banks)

# Calculate multiple metrics for each bank
metrics = []
for bank in comparison_banks:
    bank_data = df[df['bank_name'] == bank]

    # Geographic spread
    lat_range = bank_data['lat'].max() - bank_data['lat'].min()
    long_range = bank_data['long'].max() - bank_data['long'].min()
    geo_spread = lat_range + long_range

    # Baku vs Regional
    baku_pct = (bank_data['region'] == 'Baku').sum() / len(bank_data) * 100

    # Average competitive intensity
    avg_intensity = np.mean(intensity_data[bank])

    metrics.append({
        'Bank': bank,
        'Branch_Count': len(bank_data),
        'Geographic_Spread': geo_spread,
        'Baku_Percentage': baku_pct,
        'Avg_Competitive_Intensity': avg_intensity
    })

metrics_df = pd.DataFrame(metrics)

# Normalize metrics for radar chart
metrics_normalized = metrics_df.copy()
for col in ['Branch_Count', 'Geographic_Spread', 'Baku_Percentage', 'Avg_Competitive_Intensity']:
    max_val = metrics_normalized[col].max()
    if max_val > 0:
        metrics_normalized[col] = metrics_normalized[col] / max_val * 100

# Create radar chart
categories = ['Branch Count', 'Geographic\\nSpread', 'Baku\\nFocus', 'Competitive\\nIntensity']
N = len(categories)

fig = plt.figure(figsize=(18, 8))
ax1 = plt.subplot(121, projection='polar')
ax2 = plt.subplot(122)

angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]

# Plot each bank
for idx, row in metrics_normalized.iterrows():
    values = row[['Branch_Count', 'Geographic_Spread', 'Baku_Percentage',
                 'Avg_Competitive_Intensity']].values.tolist()
    values += values[:1]

    if row['Bank'] == 'Bank of Baku':
        ax1.plot(angles, values, 'o-', linewidth=3, label=row['Bank'], color='#e74c3c')
        ax1.fill(angles, values, alpha=0.15, color='#e74c3c')
    else:
        ax1.plot(angles, values, 'o-', linewidth=1.5, label=row['Bank'], alpha=0.7)

ax1.set_xticks(angles[:-1])
ax1.set_xticklabels(categories, fontsize=10)
ax1.set_ylim(0, 100)
ax1.set_title('Multi-Metric Comparison: Bank of Baku vs Leaders\\n(Normalized to 100)',
             fontsize=13, fontweight='bold', pad=20)
ax1.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=9)
ax1.grid(True)

# Comparison table
ax2.axis('tight')
ax2.axis('off')

table_data = []
for idx, row in metrics_df.iterrows():
    table_data.append([
        row['Bank'],
        f"{int(row['Branch_Count'])}",
        f"{row['Geographic_Spread']:.2f}",
        f"{row['Baku_Percentage']:.1f}%",
        f"{row['Avg_Competitive_Intensity']:.1f}"
    ])

table = ax2.table(cellText=table_data,
                 colLabels=['Bank', 'Branches', 'Geo Spread', 'Baku %', 'Comp. Intensity'],
                 cellLoc='center',
                 loc='center',
                 bbox=[0, 0, 1, 1])

table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 2)

# Color Bank of Baku row
for i, row in enumerate(table_data):
    if row[0] == 'Bank of Baku':
        for j in range(5):
            table[(i+1, j)].set_facecolor('#ffcccc')

# Header style
for j in range(5):
    table[(0, j)].set_facecolor('#3498db')
    table[(0, j)].set_text_props(weight='bold', color='white')

ax2.set_title('Detailed Metrics Comparison', fontsize=13, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('charts/14_multimetric_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"✓ Chart 14 saved")
print()

# ============================================================================
# Chart 15: Strategic Recommendations Summary
# ============================================================================
print("Generating Chart 15: Strategic Recommendations Summary...")

fig = plt.figure(figsize=(16, 10))
gs = fig.add_gridspec(3, 3, hspace=0.4, wspace=0.3)

# 1. Current Position
ax1 = fig.add_subplot(gs[0, :])
ax1.axis('off')
ax1.text(0.5, 0.8, 'BANK OF BAKU - STRATEGIC POSITION SUMMARY',
         ha='center', fontsize=18, fontweight='bold', transform=ax1.transAxes)

summary_text = f"""
CURRENT MARKET POSITION:
• Market Rank: #{bob_rank} out of {df['bank_name'].nunique()} banks
• Total Branches: {bob_count}
• Market Share: {bob_count/total_count*100:.1f}%
• Gap to Leader: {branch_counts.max() - bob_count} branches behind Kapital Bank

GEOGRAPHIC FOOTPRINT:
• Baku Concentration: {bob_region['Baku']}/{bob_count} branches ({bob_region['Baku']/bob_count*100:.1f}%)
• Regional Presence: {bob_region['Regions']}/{bob_count} branches ({bob_region['Regions']/bob_count*100:.1f}%)
• Average Competitive Intensity: {bob_avg_intensity:.1f} competitors within 10km
"""

ax1.text(0.05, 0.4, summary_text, ha='left', va='top', fontsize=11,
         transform=ax1.transAxes, family='monospace',
         bbox=dict(boxstyle='round', facecolor='#ecf0f1', alpha=0.8))

# 2. Key Metrics Comparison
ax2 = fig.add_subplot(gs[1, 0])
metric_comparison = pd.DataFrame({
    'Metric': ['Branches', 'Market\\nShare %', 'Regional\\nCoverage %'],
    'Bank of Baku': [bob_count, bob_count/total_count*100, bob_region['Regions']/bob_count*100],
    'Industry Avg': [
        df.groupby('bank_name').size().mean(),
        100/df['bank_name'].nunique(),
        df.groupby('bank_name')['region'].apply(lambda x: (x=='Regions').sum()/len(x)*100).mean()
    ]
})

x = np.arange(len(metric_comparison))
width = 0.35
ax2.bar(x - width/2, metric_comparison['Bank of Baku'], width, label='Bank of Baku', color='#e74c3c')
ax2.bar(x + width/2, metric_comparison['Industry Avg'], width, label='Industry Avg', color='#3498db')
ax2.set_ylabel('Value', fontsize=10)
ax2.set_title('Key Metrics vs Industry Average', fontsize=11, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(metric_comparison['Metric'], fontsize=9)
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3, axis='y')

# 3. Expansion Opportunities
ax3 = fig.add_subplot(gs[1, 1])
opportunity_summary = pd.DataFrame({
    'Type': ['High Gap\\nAreas', 'Underserved\\nClusters', 'Regional\\nExpansion'],
    'Count': [len(gaps), (cluster_df['BoB_Share'] < 5).sum() if 'BoB_Share' in cluster_df.columns else 0,
             df.groupby('bank_name')['region'].apply(lambda x: (x=='Regions').sum()).max() - bob_region['Regions']]
})

ax3.bar(opportunity_summary['Type'], opportunity_summary['Count'], color='#f39c12', edgecolor='black', linewidth=1.5)
ax3.set_ylabel('Number of Opportunities', fontsize=10)
ax3.set_title('Expansion Opportunity Areas', fontsize=11, fontweight='bold')
ax3.tick_params(axis='x', labelsize=9)

for i, v in enumerate(opportunity_summary['Count']):
    ax3.text(i, v + 1, str(int(v)), ha='center', fontweight='bold')
ax3.grid(True, alpha=0.3, axis='y')

# 4. Competitive Positioning
ax4 = fig.add_subplot(gs[1, 2])
nearest_top5 = nearest_comp_counts.head(5)
ax4.pie(nearest_top5.values, labels=nearest_top5.index, autopct='%1.0f%%',
        startangle=90, textprops={'fontsize': 8})
ax4.set_title('Most Frequent Direct\\nCompetitors', fontsize=11, fontweight='bold')

# 5. Recommendations
ax5 = fig.add_subplot(gs[2, :])
ax5.axis('off')

recommendations = f"""
🎯 STRATEGIC RECOMMENDATIONS FOR BANK OF BAKU:

1. REGIONAL EXPANSION (Priority: HIGH)
   • Current regional coverage ({bob_region['Regions']/bob_count*100:.1f}%) is below industry average
   • Identified {len(gaps)} high-potential locations where competitors operate but Bank of Baku is absent
   • Focus on underserved regional areas to increase market coverage

2. STRATEGIC LOCATION SELECTION (Priority: HIGH)
   • Target the top 20 recommended expansion coordinates identified in Growth Opportunity Analysis
   • These locations balance: (a) distance from existing BoB branches, (b) proximity to competitor activity
   • Prioritize areas with significant distance from nearest Bank of Baku branch

3. COMPETITIVE POSITIONING (Priority: MEDIUM)
   • Main competitors in proximity: {', '.join(nearest_top5.index[:3].tolist())}
   • Average competitive intensity: {bob_avg_intensity:.1f} competitors within 10km
   • Consider differentiation strategy to stand out in competitive markets

4. MARKET SHARE GROWTH PATH (Priority: MEDIUM)
   • To reach 10% market share: Need {int(total_count * 0.10) - bob_count} additional branches
   • Recommended balanced approach: 60% in regional areas, 40% in Baku suburbs

5. OPTIMIZATION OPPORTUNITIES (Priority: LOW)
   • Evaluate performance of existing branches in highly competitive areas
   • Consider relocating underperforming branches to gap areas
   • Leverage digital channels to extend reach without physical expansion
"""

ax5.text(0.05, 0.95, recommendations, ha='left', va='top', fontsize=9.5,
         transform=ax5.transAxes, family='monospace',
         bbox=dict(boxstyle='round', facecolor='#e8f5e9', alpha=0.9))

plt.suptitle('Bank of Baku - Strategic Analysis & Actionable Recommendations',
             fontsize=16, fontweight='bold', y=0.98)
plt.savefig('charts/15_strategic_recommendations.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"✓ Chart 15 saved")
print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 80)
print("ANALYSIS COMPLETE!")
print("=" * 80)
print()
print(f"✓ All 15 charts saved to charts/ directory")
print()
print("Charts generated:")
print("  1. Branch Count Comparison")
print("  2. Market Share Analysis")
print("  3. Geographic Distribution - All Banks")
print("  4. Bank of Baku vs Top Competitors")
print("  5. Regional Clustering Analysis")
print("  6. Baku City Analysis")
print("  7. Baku vs Regions Coverage")
print("  8. Competitive Density Analysis")
print("  9. Gap Analysis - Underserved Areas")
print(" 10. Nearest Competitor Analysis")
print(" 11. Competitive Intensity Index")
print(" 12. Market Share by Geographic Quadrants")
print(" 13. Growth Opportunity Score")
print(" 14. Multi-Metric Comparison")
print(" 15. Strategic Recommendations Summary")
print()
print("=" * 80)
print("KEY INSIGHTS FOR BANK OF BAKU:")
print("=" * 80)
print(f"• Current Position: Rank #{bob_rank} with {bob_count} branches ({bob_count/total_count*100:.1f}% market share)")
print(f"• Baku Concentration: {bob_region['Baku']/bob_count*100:.1f}% of branches")
print(f"• Expansion Opportunities: {len(gaps)} high-potential locations identified")
print(f"• Competitive Intensity: {bob_avg_intensity:.1f} competitors within 10km average")
print(f"• Growth Target: {int(total_count * 0.10) - bob_count} branches needed for 10% market share")
print("=" * 80)
