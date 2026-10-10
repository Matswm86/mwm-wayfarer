"""Wayfarer GDD v2 fire and warmth numbers (my calc). Run: python3 tools/fire_calc.py

Time: 1 in-game hour = 60 real seconds. A night (20:00-06:00) = 10 in-game hours.
All constants mirror GDD v2 section 5 (fire). Change them there and here together.
"""

FIRE_SIZE = {  # burn kg/h with branch wood in calm air, warm radius m
    "small": (1.5, 2.5),
    "camp": (3.0, 5.0),
    "big": (6.0, 8.0),
}
FUEL_DURATION = {  # x burn time vs branch wood (higher = slower)
    "dry grass/dung": 0.4,
    "twigs": 0.6,
    "branch wood": 1.0,
    "split logs": 1.3,
    "peat": 1.2,
    "charcoal": 2.0,
}
FIRE_WARM_MAX = 30.0  # Warmth/h at the fire centre at Heat 100
SIT_DIST = 1.5  # m, where the player sits
LOSS = {"mild": 0, "cool": -4, "cold": -8, "freezing": -14}
WET, NIGHT = -6, -3
WIND_LOSS = -3  # per unit wind 0..1
CLOTHING = {"none (hominin)": 0.0, "hide wrap": 0.3, "sewn furs": 0.5, "wool + oilskin": 0.6}


def burn_rate(size: str, fuel: str, wind: float, windbreak: bool) -> float:
    base, _ = FIRE_SIZE[size]
    w = wind * (0.5 if windbreak else 1.0)
    return base * (1 + 0.5 * w) / FUEL_DURATION[fuel]


def fire_warmth(size: str, heat: float, dist: float = SIT_DIST) -> float:
    _, radius = FIRE_SIZE[size]
    return max(0.0, FIRE_WARM_MAX * (1 - dist / radius) * heat / 100)


def warmth_rate(band: str, wet: bool, wind: float, clothing: str, shelter: bool,
                fire: tuple[str, float] | None) -> float:
    loss = LOSS[band] + NIGHT + (0 if shelter else (WET if wet else 0) + WIND_LOSS * wind)
    loss *= 1 - CLOTHING[clothing]
    gain = fire_warmth(*fire) if fire else 0.0
    return loss + gain


print("Fuel for one 10 h night (kg), camp fire")
print(f"{'fuel':16} {'calm':>6} {'wind 0.6 open':>14} {'wind 0.6 + windbreak':>21}")
for f in FUEL_DURATION:
    r = [10 * burn_rate("camp", f, w, b) for w, b in ((0, False), (0.6, False), (0.6, True))]
    print(f"{f:16} {r[0]:6.1f} {r[1]:14.1f} {r[2]:21.1f}")

print("\nWarmth change per in-game hour at night, sitting 1.5 m from the fire")
cases = [
    ("Era 1-2, cool night, no fire, no clothes", "cool", False, 0.3, "none (hominin)", False, None),
    ("Era 2, cool night, camp fire heat 80", "cool", False, 0.3, "none (hominin)", False, ("camp", 80)),
    ("Era 4, freezing, wet, windy, no fire", "freezing", True, 0.6, "sewn furs", False, None),
    ("Era 4, freezing, windbreak shelter, camp fire 80", "freezing", True, 0.6, "sewn furs", True, ("camp", 80)),
    ("Era 10, cold rain night outdoors, wool", "cold", True, 0.6, "wool + oilskin", False, None),
    ("Era 10, cold, in house, hearth (camp) 60", "cold", False, 0.0, "wool + oilskin", True, ("camp", 60)),
    ("Era 10, cold, outdoors, small fire 80", "cold", True, 0.6, "wool + oilskin", False, ("small", 80)),
]
for name, *args in cases:
    r = warmth_rate(*args)
    hours_to_zero = (100 / -r) if r < 0 else float("inf")
    print(f"{name:52} {r:+6.1f}/h   100->0 in {hours_to_zero:5.1f} h")

print("\nEmber carrier life (in-game h; x0.5 in rain unless covered)")
for n, h in (("smouldering branch", 1), ("tinder fungus / dung wrap", 4), ("horn or clay ember pot", 12)):
    print(f"{n:28} {h:3} h = {h} real min dry, {h / 2:.1f} real min in rain")
