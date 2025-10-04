import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df1 = pd.read_csv('stale_rate_data.csv')
plt.figure(figsize=(10, 6))
plt.plot(df1.iloc[:,0], df1.iloc[:,1], color='#1f77b4', marker='o', linewidth=2, markersize=6)
plt.xscale('log')
plt.xlabel('$c$', fontsize=12)
plt.ylabel(r"$p_\text{stale}$", fontsize=12)
plt.ylim(2e-5, 7e-5)
plt.grid(True, alpha=0.3)
if df1.iloc[:,1].max() < 0.001:
    plt.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
label = '(a)'
plt.text(0.5, -0.15, label, fontsize=16, ha='center', va='top', transform=plt.gca().transAxes)
plt.tight_layout()
plt.savefig('images/fixed_stale_rate.png', dpi=300)

df2 = pd.read_csv('threshold_51_data.csv')
plt.figure(figsize=(10, 6))
plt.plot(df2.iloc[:,0], df2.iloc[:,1], color='#d62728', marker='o', linewidth=2, markersize=6)
plt.xscale('log')
plt.xlabel('$c$', fontsize=12)
plt.ylabel("51% attack threshold", fontsize=12)
plt.ylim(0.4999, 0.5001)
plt.grid(True, alpha=0.3)
if df2.iloc[:,1].max() < 0.001:
    plt.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
label = '(b)'
plt.text(0.5, -0.15, label, fontsize=16, ha='center', va='top', transform=plt.gca().transAxes)
plt.tight_layout()
plt.savefig('images/fixed_51_attack_threshold.png', dpi=300)

df3 = pd.read_csv('blocks_per_day_data.csv')
plt.figure(figsize=(10, 6))
plt.plot(df3.iloc[:,0], df3.iloc[:,1], color='#2ca02c', marker='o', linewidth=2, markersize=6)
plt.xscale('log')
plt.xlabel('$c$', fontsize=12)
plt.ylabel("Blocks mined per day", fontsize=12)
plt.grid(True, alpha=0.3)
if df3.iloc[:,1].max() < 0.001:
    plt.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
label = '(c)'
plt.text(0.5, -0.15, label, fontsize=16, ha='center', va='top', transform=plt.gca().transAxes)
plt.tight_layout()
plt.savefig('images/fixed_blocks_per_day.png', dpi=300)

df4 = pd.read_csv('forks_per_day_data.csv')
plt.figure(figsize=(10, 6))
plt.plot(df4.iloc[:,0], df4.iloc[:,1], color='#ff7f0e', marker='o', linewidth=2, markersize=6)
plt.xscale('log')
plt.xlabel('$c$', fontsize=12)
plt.ylabel("Forks per day", fontsize=12)
plt.grid(True, alpha=0.3)
if df4.iloc[:,1].max() < 0.001:
    plt.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
label = '(d)'
plt.text(0.5, -0.15, label, fontsize=16, ha='center', va='top', transform=plt.gca().transAxes)
plt.tight_layout()
plt.savefig('images/fixed_forks_per_day.png', dpi=300)

df5 = pd.read_csv('quantum_blocks_data.csv')
plt.figure(figsize=(10, 6))
plt.plot(df5.iloc[:,0], df5.iloc[:,1], color='#9467bd', marker='o', linewidth=2, markersize=6)
plt.xscale('log')
plt.xlabel('$c$', fontsize=12)
plt.ylabel("Blocked mined by quantum miners per day", fontsize=12)
plt.grid(True, alpha=0.3)
if df5.iloc[:,1].max() < 0.001:
    plt.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
label = '(e)'
plt.text(0.5, -0.15, label, fontsize=16, ha='center', va='top', transform=plt.gca().transAxes)
plt.tight_layout()
plt.savefig('images/fixed_quantum_blocks_per_day.png', dpi=300)

df6 = pd.read_csv('quantum_percentage_data.csv')
plt.figure(figsize=(10, 6))
plt.plot(df6.iloc[:,0], df6.iloc[:,1], color='#8c564b', marker='o', linewidth=2, markersize=6)
plt.xscale('log')
plt.xlabel('$c$', fontsize=12)
plt.ylabel("% of blocks mined by quantum miners", fontsize=12)
plt.grid(True, alpha=0.3)
if df6.iloc[:,1].max() < 0.001:
    plt.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
label = '(f)'
plt.text(0.5, -0.15, label, fontsize=16, ha='center', va='top', transform=plt.gca().transAxes)
plt.tight_layout()
plt.savefig('images/fixed_quantum_percentage.png', dpi=300)

fig, axes = plt.subplots(2, 3, figsize=(18, 12))

ax1 = axes[0, 0]
ax1.plot(df1.iloc[:,0], df1.iloc[:,1], color='#1f77b4', marker='o', linewidth=2, markersize=6)
ax1.set_xscale('log')
ax1.set_xlabel('$c$', fontsize=12)
ax1.set_ylabel(r"$p_\text{stale}$", fontsize=12)
ax1.set_ylim(2e-5, 7e-5)
ax1.grid(True, alpha=0.3)
if df1.iloc[:,1].max() < 0.001:
    ax1.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
ax1.text(0.5, -0.25, '(a)', fontsize=16, ha='center', va='top', transform=ax1.transAxes)

ax2 = axes[0, 1]
ax2.plot(df2.iloc[:,0], df2.iloc[:,1], color='#d62728', marker='o', linewidth=2, markersize=6)
ax2.set_xscale('log')
ax2.set_xlabel('$c$', fontsize=12)
ax2.set_ylabel("51% attack threshold", fontsize=12)
ax2.set_ylim(0.4999, 0.5001)
ax2.grid(True, alpha=0.3)
if df2.iloc[:,1].max() < 0.001:
    ax2.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
ax2.text(0.5, -0.25, '(b)', fontsize=16, ha='center', va='top', transform=ax2.transAxes)

ax3 = axes[0, 2]
ax3.plot(df3.iloc[:,0], df3.iloc[:,1], color='#2ca02c', marker='o', linewidth=2, markersize=6)
ax3.set_xscale('log')
ax3.set_xlabel('$c$', fontsize=12)
ax3.set_ylabel("Blocks mined per day", fontsize=12)
ax3.grid(True, alpha=0.3)
if df3.iloc[:,1].max() < 0.001:
    ax3.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
ax3.text(0.5, -0.25, '(c)', fontsize=16, ha='center', va='top', transform=ax3.transAxes)

ax4 = axes[1, 0]
ax4.plot(df4.iloc[:,0], df4.iloc[:,1], color='#ff7f0e', marker='o', linewidth=2, markersize=6)
ax4.set_xscale('log')
ax4.set_xlabel('$c$', fontsize=12)
ax4.set_ylabel("Forks per day", fontsize=12)
ax4.grid(True, alpha=0.3)
if df4.iloc[:,1].max() < 0.001:
    ax4.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
ax4.text(0.5, -0.25, '(d)', fontsize=16, ha='center', va='top', transform=ax4.transAxes)

ax5 = axes[1, 1]
ax5.plot(df5.iloc[:,0], df5.iloc[:,1], color='#9467bd', marker='o', linewidth=2, markersize=6)
ax5.set_xscale('log')
ax5.set_xlabel('$c$', fontsize=12)
ax5.set_ylabel("Blocks mined by quantum miners per day", fontsize=12)
ax5.grid(True, alpha=0.3)
if df5.iloc[:,1].max() < 0.001:
    ax5.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
ax5.text(0.5, -0.25, '(e)', fontsize=16, ha='center', va='top', transform=ax5.transAxes)

ax6 = axes[1, 2]
ax6.plot(df6.iloc[:,0], df6.iloc[:,1], color='#8c564b', marker='o', linewidth=2, markersize=6)
ax6.set_xscale('log')
ax6.set_xlabel('$c$', fontsize=12)
ax6.set_ylabel("% of blocks mined by quantum miners", fontsize=12)
ax6.grid(True, alpha=0.3)
if df6.iloc[:,1].max() < 0.001:
    ax6.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
ax6.text(0.5, -0.25, '(f)', fontsize=16, ha='center', va='top', transform=ax6.transAxes)

plt.tight_layout()
plt.subplots_adjust(top=0.93, hspace=0.35)
plt.savefig('images/fixed_iter_plots_combined.png', dpi=300, bbox_inches='tight')
plt.show()