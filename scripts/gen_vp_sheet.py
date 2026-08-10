"""Generate the per-checkpoint fuelling/hydration sheet for Berlin Mauerweglauf 2026.

VP names, km marks and individual cut-offs are the official 2026 table from
100meilen.de (counter-clockwise course). Everything else is derived from
analyses/races/2026-08-10-berlin-hydration-execution-card.md.
"""

import csv

START_MIN = 6 * 60  # 06:00

# (vp label, name, km, individual cutoff in minutes from midnight of race day)
VPS = [
    ("Start", "Friedrich-Ludwig-Jahnsportpark", 0.0, None),
    ("VP 1", "S-Bahnhof Wilhelmsruh", 7.7, 7 * 60 + 17),
    ("VP 2", "Lauftreff Lübars", 13.3, 8 * 60 + 14),
    ("VP 3", "Oranienburger Chaussee", 18.8, 9 * 60 + 9),
    ("VP 4", "Hohen Neuendorf", 23.1, 9 * 60 + 53),
    ("VP 5", "Frohnau", 27.8, 10 * 60 + 40),
    ("VP 6 / WP 1", "Ruderclub Oberhavel — DROP BAG 1", 33.1, 11 * 60 + 34),
    ("VP 7", "Grenzturm Nieder Neuendorf", 37.9, 12 * 60 + 22),
    ("VP 8", "Schönwalde", 45.2, 13 * 60 + 36),
    ("VP 9", "Falkenseer Chaussee", 51.0, 14 * 60 + 35),
    ("VP 10", "Karolinenhöhe", 57.8, 15 * 60 + 43),
    ("VP 11", "Pagel & Friends", 62.5, 16 * 60 + 31),
    ("VP 12 / WP 2", "Schloss Sacrow — DROP BAG 2", 70.2, 17 * 60 + 49),
    ("VP 13", "Revierförsterei Krampnitz", 76.1, 18 * 60 + 48),
    ("VP 14", "Brauhaus Meierei", 81.9, 19 * 60 + 47),
    ("VP 15", "Gedenkstätte Griebnitzsee", 89.0, 20 * 60 + 58),
    ("VP 16", "Königsweg", 95.8, 22 * 60 + 20),
    ("VP 17 / WP 3", "Sportplatz Teltow — DROP BAG 3", 102.0, 23 * 60 + 34),
    ("VP 18", "Osdorfer Straße", 108.8, 24 * 60 + 43),
    ("VP 19", "Lichtenrade", 115.0, 25 * 60 + 57),
    ("VP 20", "Buckow", 123.7, 27 * 60 + 42),
    ("VP 21", "Rudow", 130.6, 29 * 60 + 5),
    ("VP 22", "Johannisthaler Chaussee", 136.5, 30 * 60 + 15),
    ("VP 23", "Dammweg", 142.2, 31 * 60 + 31),
    ("VP 24", "East Side Gallery", 148.1, 32 * 60 + 50),
    ("VP 25", "Checkpoint Charlie", 152.8, 33 * 60 + 53),
    ("VP 26", "Gedenkstätte Günter Litfin", 157.3, 34 * 60 + 53),
    ("Ziel", "Friedrich-Ludwig-Jahnsportpark", 162.1, 36 * 60),
]

# Blocks: (label, km_end, pace min/km incl. stops, ml/h total, mix share, carb% of mix)
# mix share = fraction of fluid taken as U Sport at full strength (100 g/L)
BLOCKS = [
    ("A", 33.1, 6.344, 750, 1.00),
    ("B", 51.0, 6.874, 800, 1.00),      # mix only up to the VP 9 step-down
    ("B", 70.2, 6.874, 800, 2 / 3),     # 2 mix : 1 water
    ("C", 102.0, 7.547, 950, 2 / 3),    # 2 mix : 1 water
    ("D", 128.0, 7.500, 800, 3 / 4),    # 3 mix : 1 water
    ("E", 162.1, 8.563, 600, 1.00),
]

# ECMWF IFS hourly air temperature, race day (clock hour -> °C)
TEMPS = {
    6: 20.4, 7: 21.0, 8: 22.4, 9: 24.9, 10: 28.1, 11: 31.0, 12: 33.1,
    13: 34.9, 14: 36.1, 15: 36.7, 16: 36.8, 17: 36.5, 18: 35.9, 19: 34.8,
    20: 33.5, 21: 31.6, 22: 29.4, 23: 27.5, 24: 26.2, 25: 25.2, 26: 24.2,
}

TABLET = "1 U Hydrate → water flask"
CHEWS = "2 FastChews (dry)"


def salt_for(vp, km, clock):
    """Salt is pinned to VPs, not to the clock — legs run 30-65 min, so an
    hourly cadence drifts off the stops and silently under-doses. Alternating
    tablet/chews at every VP through the hot block averages ~430 mg/h on top of
    the ~450-510 mg/h the mix already carries: mid-band for 32-37 C."""
    if km < 33.1:
        return "—  (mix carries it)"
    if km < 51.0:  # VP 6-8, mix still full strength, 26-31 C
        return CHEWS if vp in ("VP 6 / WP 1", "VP 8") else "—"
    if km < 130.6:  # VP 9-20, the hot block
        n = int(vp.split()[1])
        return TABLET if n % 2 else CHEWS
    if vp in ("VP 21", "VP 24"):  # night, cooling, mix at full strength again
        return TABLET
    return "—"

NOTES = {
    "VP 5": "Last cool VP. Start dousing here if not already.",
    "VP 6 / WP 1": "ICE → both mix flasks first, then bandana. 4 × 90 g out. Sunscreen. Shoe abort decision (Evo SL).",
    "VP 8": "DE-ESCALATION CHECK. If it is clearly staying under 30 °C, hold mix-only all day and drop the water ratio.",
    "VP 9": "RATIO STEP-DOWN → 2 mix : 1 water. First honest read on whether 10 % is sitting well in heat — 19 km to adjust before the crux.",
    "VP 12 / WP 2": "ICE → flasks first. 4 × 90 g out. THE decision point: hip, posture, GI, urine, cooling. Take the time.",
    "VP 16": "Last VP before the drop bag. Check you can reach Teltow on what you carry.",
    "VP 17 / WP 3": "NIGHT GEAR. 6 × 90 g out — 60 km on this bag. First caffeine 100 mg. Thermos = cold water, ice is a bonus. Ratio eases to 3:1.",
    "VP 20": "Dörferblick — walk the climb, as planned.",
    "VP 21": "Headlamp + reflective vest ON by here (mandatory 21:00–06:00). Back to mix only.",
    "VP 24": "U Intend 250 mg.",
    "Ziel": "Done.",
}


def block_for(km):
    for label, km_end, pace, ml_h, mix_share in BLOCKS:
        if km < km_end - 1e-9:
            return label, pace, ml_h, mix_share
    return BLOCKS[-1][0], BLOCKS[-1][2], BLOCKS[-1][3], BLOCKS[-1][4]


def hhmm(minutes):
    minutes = int(round(minutes))
    return f"{(minutes // 60) % 24:02d}:{minutes % 60:02d}"


def temp_at(minutes):
    h = minutes / 60.0
    lo = int(h)
    frac = h - lo
    a = TEMPS.get(lo, TEMPS[26])
    b = TEMPS.get(lo + 1, TEMPS[26])
    return a + frac * (b - a)


rows = []
clock = START_MIN
mix_ml_cum = 0.0
portions_used = 0
salt_due_at = None

for i, (vp, name, km, cutoff) in enumerate(VPS):
    if i > 0:
        prev_km = VPS[i - 1][2]
        _, pace, _, _ = block_for(prev_km)
        clock += (km - prev_km) * pace

    block, _, _, _ = block_for(km)
    temp = temp_at(clock)

    # the leg FROM this VP to the next
    if i < len(VPS) - 1:
        nxt_km = VPS[i + 1][2]
        leg_km = nxt_km - km
        _, pace, ml_h, mix_share = block_for(km)
        leg_min = leg_km * pace
        leg_ml = ml_h * leg_min / 60.0
        leg_mix = leg_ml * mix_share
        leg_water = leg_ml - leg_mix
        leg_carb = leg_mix * 0.10  # 100 g/L at full strength

        before = int(mix_ml_cum // 900)
        mix_ml_cum += leg_mix
        after = int(mix_ml_cum // 900)
        new_portions = after - before
        portions_used = after
        portion_note = f"YES × {new_portions}" if new_portions else "no — top up"
    else:
        leg_km = leg_min = leg_ml = leg_mix = leg_water = leg_carb = 0.0
        portion_note = "—"

    salt = salt_for(vp, km, clock) if i < len(VPS) - 1 else "—"

    if block == "A":
        cooling = "—" if km < 20 else "douse head/neck/arms"
    elif block in ("B", "C", "D"):
        cooling = "douse + rewet bandana, cap, sleeves"
        if block == "C":
            cooling = "MAX — douse + rewet + ice if you have it"
    else:
        cooling = "douse + rewet" if clock < 23 * 60 else "—"

    margin = ""
    if cutoff is not None:
        m = cutoff - clock
        margin = f"+{int(m // 60)}:{int(m % 60):02d}"

    rows.append(
        {
            "VP": vp,
            "Name": name,
            "Km": f"{km:.1f}",
            "Leg to next (km)": f"{leg_km:.1f}" if leg_km else "",
            "ETA": hhmm(clock),
            "Cut-off": hhmm(cutoff) if cutoff else "",
            "Margin": margin,
            "Air °C": f"{temp:.0f}",
            "Block": block,
            "Drink on leg (ml)": f"{leg_ml:.0f}" if leg_ml else "",
            "of which MIX (ml)": f"{leg_mix:.0f}" if leg_ml else "",
            "of which WATER (ml)": f"{leg_water:.0f}" if leg_ml else "",
            "Ratio": {1.0: "mix only", 2 / 3: "2 mix : 1 water", 3 / 4: "3 mix : 1 water"}[
                block_for(km)[3]
            ]
            if leg_ml
            else "",
            "Carbs on leg (g)": f"{leg_carb:.0f}" if leg_ml else "",
            "Carry vs 1350 ml": f"{leg_ml / 1350 * 100:.0f}%" if leg_ml else "",
            "Fresh 90 g portion here?": portion_note,
            "Salt at this VP": salt,
            "Cooling at this VP": cooling,
            "Notes": NOTES.get(vp, ""),
        }
    )

out = "/Users/patrikakselsson/Projects/ClaudeCoach/analyses/races/2026-08-10-berlin-checkpoint-fuelling.csv"
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

tot_ml = sum(float(r["Drink on leg (ml)"] or 0) for r in rows)
tot_mix = sum(float(r["of which MIX (ml)"] or 0) for r in rows)
tot_water = sum(float(r["of which WATER (ml)"] or 0) for r in rows)
tot_carb = sum(float(r["Carbs on leg (g)"] or 0) for r in rows)
print(f"rows: {len(rows)}")
print(f"total fluid  {tot_ml/1000:.1f} L   mix {tot_mix/1000:.1f} L   water {tot_water/1000:.1f} L")
print(f"total carbs from drink: {tot_carb:.0f} g over 19.9 h = {tot_carb/19.87:.0f} g/h avg")
print(f"portions consumed: {portions_used}  (mix ml {mix_ml_cum:.0f})")

# mix needed out of each drop bag, to reach the next one
bounds = [(0.0, 33.1, "start vest"), (33.1, 70.2, "bag 1 / km 33"),
          (70.2, 102.0, "bag 2 / km 70"), (102.0, 162.1, "bag 3 / km 102")]
for lo, hi, label in bounds:
    ml = sum(float(r["of which MIX (ml)"] or 0) for r in rows
             if lo <= float(r["Km"]) < hi)
    print(f"  {label:<16} {ml:5.0f} ml mix -> {ml/900:.1f} portions needed")

longest = max(rows[:-1], key=lambda r: float(r["Drink on leg (ml)"] or 0))
print(f"longest carry: {longest['VP']} -> next, {longest['Drink on leg (ml)']} ml "
      f"({longest['Carry vs 1350 ml']} of 3 flasks)")
tabs = sum(1 for r in rows if "U Hydrate" in r["Salt at this VP"])
chews = sum(1 for r in rows if "FastChews" in r["Salt at this VP"])
print(f"salt: {tabs} U Hydrate, {chews} FastChews stops")
print(f"written: {out}")
