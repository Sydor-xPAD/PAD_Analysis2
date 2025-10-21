import re
import pandas as pd

g_headers = ["Time_Epoch","Seconds", "ecur", "ic1_diode", "VBPM_VER",\
           "VPPM_HOR","xx", "yy", "laserv", "aux1", "ic2", "ic4", "vibe1_pos", \
            "vine1_neg", "vibe2_pos", "vibe2_neg", "ic0", "ic3" ]			
					
def parse_tseries_file(filename):
    shots = {}
    with open(filename, 'r') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 1️⃣ Match "#S <number> tseries 10 0.5 0"
        m = re.match(r"#S\s+(\d+)\s+tseries\s+10\s+0\.5\s+0", line)
        if m:
            shot_number = int(m.group(1))
            i += 1

            # 2️⃣ Advance to the "#L ..." line
            while i < len(lines) and not lines[i].startswith("#L "):
                i += 1
            if i >= len(lines):
                break

            ## Parse headers
            #headers = lines[i].strip().split()[1:]  # skip '#L'
            headers = g_headers
            i += 1

            # 3️⃣ Read numeric data rows until '#C'
            data_rows = []
            while i < len(lines):
                l = lines[i].strip()
                if l.startswith("#C") or l.startswith("#S "):
                    break
                if not l.startswith("#") and l != "":
                    data_rows.append(l)
                i += 1

            # Convert rows to DataFrame
            data = [list(map(float, row.split())) for row in data_rows]
            df = pd.DataFrame(data, columns=headers)
            shots[shot_number] = df

        else:
            i += 1

    return shots


# Example usage:
shots = parse_tseries_file("/Users/yoram/Sydor/PAD_Analysis/YFPlayground/Keck020_LLNL/truncated_spec.log")

# You can access each shot’s DataFrame by shot number:
#for shot, df in shots.items():
#    print(f"Shot {shot}: {len(df)} rows")
#    print(df.head(), "\n")

#plot shot# versus ic3
import matplotlib.pyplot as plt

# Compute per-shot means
shot_numbers = sorted(shots.keys())
ic3_means = [shots[s]["ic3"].mean() for s in shot_numbers]
ic0_means = [shots[s]["ic0"].mean()  for s in shot_numbers]
ic2_means = [shots[s]["ic2"].mean()  for s in shot_numbers]
# 1.720 is arbitrary scaling factor to align the two series visually

# Plot both series
plt.figure(figsize=(8, 5))
plt.plot(shot_numbers, ic3_means, marker='o', label='ic3')
plt.plot(shot_numbers, ic0_means, marker='s', label='ic0')
plt.plot(shot_numbers, ic2_means, marker='s', label='ic2')


plt.xlabel("Shot Number")
plt.ylabel("Mean value")
plt.title("Mean ic0 and ic3 vs Shot Number")
#plt.ylim(8000, 140000)   # <-- set Y scale range
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()


# Help me get average ic0 over specifiec shot ranges:
def average_ic0(shots, shot_ranges):
    averages = {}
    for start, end in shot_ranges:
        ic0_values = []
        for shot in range(start, end + 1):
            if shot in shots:
                ic0_values.extend(shots[shot]["ic0"].tolist())
        if ic0_values:
            averages[(start, end)] = sum(ic0_values) / len(ic0_values)
        else:
            averages[(start, end)] = None
    return averages

#computer average_ic0 for shots 441-480, 521-560, 601-640
#shot_ranges = [(441, 480), (481,520), (521,560), (561,600), (601,640), (641,680), (681,720),(721,760)]
shot_ranges = [(1262,1282), (1283,1302), (1303,1322), (1323,1342), \
               (1343,1362), (1363,1382), (1383,1402), (1403,1422), \
               (1423,1442), (1443,1462), (1463,1482), (1483,1502), \
               (1503,1522), (1523,1542), (1543,1562), (1563,1582), \
               (1583,1602), (1603,1622), (1623,1642), (1643,1662), \
               (1663,1682), (1683,1702), (1703,1722), (1723,1742), \
               (1743,1762), (1763,1782), (1783,1802), (1803,1822), \
               (1823,1842), (1843,1862), (1863,1882), (1883,1902)]
               

avg_ic0_results = average_ic0(shots, shot_ranges)
for shot_range, avg in avg_ic0_results.items():
    print(f"Average ic0 for shots {shot_range[0]}-{shot_range[1]}: {avg}")    
