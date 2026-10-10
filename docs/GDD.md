# MWM Wayfarer (working title): game design doc

Version 1, 2026-10-07, game-designer. Slug `mwm-wayfarer`. Engine-neutral: the owner picks Godot 4.6 or Unity 6 after the art drafts, so this doc names behaviours, numbers and data, never engine nodes.

Target: Android, **landscape 1920x1080** (owner), third person, realistic high-end look (owner; graphic-designer owns `docs/DESIGN.md`). Fully offline, no ads, no tracking, no live LLM, no API cost (owner).

Legend: **(owner)** = decided in `docs/BRIEF.md`, do not reopen. **(feedback)** = from the outside feedback notes in the brief. **(my calc)** = my own arithmetic (`tools/econ_calc.py`, section 12), not a source. **(my call)** = a design choice I made; change it freely. **(ask)** = open question for the owner, see section 13.

---

## 1. Pitch, pillars, players

### 1.1 Pitch
Walk, climb, swim and sail across five hand-built regions, from a Nordic fjord to a desert canyon oasis, gathering what each land offers, trading it where it is scarce, building homes and docks that make villages grow, and following rumors from the people you meet to wonders no map shows.

### 1.2 Design pillars
| # | Pillar | Test a feature must pass |
|---|---|---|
| P1 | **The world runs without you** | Does this fact come from the simulation (weather, stock, schedule, memory) rather than a script? |
| P2 | **Movement is a pleasure** | Is walking an empty field, climbing a cliff or swimming a cove satisfying with no goal at all? (feedback) |
| P3 | **Wonder is earned by curiosity** | Does the player find it by listening, looking and going, not by a quest marker? |
| P4 | **You matter by building and trading** | Does the player's work visibly change a place: prices, buildings, people, routes? |

### 1.3 Target players
| Group | What they want | What we give |
|---|---|---|
| Youth, 10-15 (my call on the age band, ask) | Freedom, climbing, discovery, a home base, friendly people | Gentle survival preset, no fail state, readable icons, short tasks |
| Adults | A believable world, economy depth, a calm long game | Hardy preset, trade routes, price play, settlement growth, lore |
| Both | Calm sessions on a phone, 15-40 min | A day in the world lasts 24 real minutes, save anywhere |

### 1.4 What the game deliberately does not have
- No combat, no weapons, no enemies, no damage from creatures. Animals are wildlife: they graze, flee, follow, or ignore you.
- No death. No health bar. Falling, cold, hunger and deep water create setbacks (slower, tired, carried home), never a game over (section 4).
- No crime, theft or stealing loop. No "evil" reputation.
- No loot drops, no character levels, no damage numbers. Growth is skills by use, tools, reputation and what you have built.
- No energy timers, no ads, no premium currency, no gacha, no login streak rewards (studio rule).
- No live text generation. Every spoken line exists at build time (owner).

---

## 2. Core loop

**Explore -> discover -> gather -> process -> trade -> build -> connect -> unlock -> explore further** (feedback). Not kill -> loot -> level.

Time scale (my call): **1 in-game day = 24 real minutes** (1 in-game minute = 1 real second). Day 06:00-20:00 = 14 real min, night 20:00-06:00 = 10 real min. Sleeping skips to 06:00.

| Scale | Length | Loop | Concrete example (fjord valley, slice 01) |
|---|---|---|---|
| Minute | 30 s - 3 min | Move -> notice -> act -> feedback | Jog up the riverbank, spot cloudberries on a slope, harvest 6 (berries pop into the basket, +1 Foraging xp tick), notice the river is brown and high, hear the fisher Ingrid grumble about it. |
| Session | 15-40 min (about one in-game day) | Plan -> gather/process -> sell -> spend -> one visible change | Morning: market board shows fresh fish at 8.7 (flood, section 5.2). You had 12 smoked fish in the smokehouse: sell at the stall for 104 coins. Buy 40 planks' worth of nails. Afternoon: raise the walls of the new house. Evening: share a meal at the longhouse, hear a rumor about singing under the falls. Sleep. |
| Week | 5-10 sessions (7 in-game days = 2.8 real h, my calc) | Grow a place -> open a route -> reach a wonder | Finish the house, a fishing family moves in, the hamlet becomes a village (section 5.10), the trader's boat starts calling every 3 days, you follow the falls rumor and find the Singing Cavern, whose resonant crystal lets the smith cast the village bell, which starts the first festival. |

Where a player stops: after sleeping (auto-save, a short "night summary" card: what changed in the village). Why they come back: a house half built, a price that will move, a rumor not yet checked, a festival in 2 days.

---

## 3. Regions

Five regions, each a dense hand-built area of about 2x2 km (feedback: "AA-sized world with depth"), linked by sea and land routes. The player's home is the fjord.

### 3.1 The five regions
| # | Region (working name) | Look | Native resources | Signature wonders | Community type | Travel in |
|---|---|---|---|---|---|---|
| R1 | **Skarvik Fjord** (Nordic fjord coast) | Steep granite walls, waterfalls, turf-roof timber houses, birch and pine, grey-green sea, long summer light, northern lights | Pine timber, granite, herring/cod, cloudberries, wool, bog iron, birch bark, tar | Singing Cavern (behind Bluewater Falls), Whale Graveyard beach, northern lights (event) | Fishing and boatbuilding hamlet, longhouse at its heart | Start region |
| R2 | **The Amberline Isles** (lost-age Mediterranean archipelago) | White limestone, terraced olive groves, overgrown marble ruins of an older age, turquoise shallows, cypress, sea caves | Olives, grapes, sea salt, marble, sponges, shell dye, figs | Forgotten Observatory, Sunken Colonnade, Sky Bridge (natural arch) | Island port towns and ruin-keepers who study the old age | Sea-going boat from R1 |
| R3 | **Redwall Oasis** (desert canyon trade oasis) | Red sandstone slot canyons, cliff dwellings, palm oasis, caravanserai courtyards, heat shimmer, huge star field | Dates, copper, glass sand, sandstone, indigo, spices (via far caravans) | Glass Forest (lightning-fused sand trees), Echo Canyon, meteor shower over the Star Well (event) | Caravan crossroads: the biggest market, traders from every region | Caravan from the R2 mainland port |
| R4 | **Greenmouth Delta** (rainforest river delta) | Mangroves, stilt villages, brown wide channels, mist, giant buttress trees, glowing fungi at night | Hardwood, cacao, reeds, pearls, medicinal herbs, rubber sap, tropical fruit | Floating Isles (drifting vegetation rafts), Glowworm Grotto, the Thousand-Root Tree | River-barge families, seasonal flood life | River barge downstream from R3 |
| R5 | **Frostspine Highlands** (glacier highlands) | Blue glacier tongues, ice caves, terraced barley, prayer-flag style cairns, hot springs steaming in snow | Yak wool/felt, rock crystal, hot-spring salts, barley, mountain moss, ice | Ice Cathedral (glacier cave), Hot Spring Terraces, Frozen Falls (winter only) | Herder villages around a stargazers' hall | Mountain pass from R1 (cold gear + pack animal) |

Each region has 6 major wonders (30 total) plus 8 timed sky/season events shared across regions (section 5.9).

### 3.2 Import/export matrix
Rows export to columns. Each cell is what flows on that route when it is open (my call).

| From \ To | R1 Fjord | R2 Isles | R3 Oasis | R4 Delta | R5 Highlands |
|---|---|---|---|---|---|
| **R1 Fjord** | - | Timber, tar, stockfish, wool | Stockfish, iron | Iron tools, tar | Timber, stockfish, iron |
| **R2 Isles** | Olive oil, salt, wine, marble | - | Oil, wine, shell dye | Salt, wine | Oil, dried figs |
| **R3 Oasis** | Glass, spices, copper | Glass, copper, dates | - | Glass, indigo, copper | Glass, spices, dates |
| **R4 Delta** | Cacao, hardwood, herbs | Hardwood, pearls | Cacao, pearls, herbs | - | Medicinal herbs, cacao |
| **R5 Highlands** | Felt, crystal | Crystal, hot-spring salts | Felt, crystal | Felt, barley | - |

Design rule: every region lacks at least one thing it needs every day (R2 has no forests, R3 has no fish, R4 has no stone or iron, R5 has no oil or fruit, R1 has no salt, grain surplus or glass). Shortage is what makes trade matter.

### 3.3 Travel and unlocks
| Route | Means | Unlock condition | Trip length (real) |
|---|---|---|---|
| R1 <-> R2 | Sea-going boat (player sails or books passage) | Build the Skarvik dock + boatwright reputation Trusted + 1 boat (120 timber, 20 tar, 30 rope, 1 sail cloth) | 3 min sailed, or 20 s skip card |
| R2 <-> R3 | Ship to the mainland port, then caravan | Merchant reputation Trusted in R2; buy a caravan berth (60 coins) | 2 min caravan ride, or skip |
| R3 <-> R4 | River barge downstream (and poled upstream) | Find the Echo Canyon wonder (its rumor names the barge landing) | 3 min, or skip |
| R1 <-> R5 | Mountain pass on foot or with a pack animal | Cold gear (felted cloak or fur-lined coat) + a pack pony; pass closed in deep winter on Hardy | 4 min walked, or skip after the first crossing |
| R5 <-> R3 | High caravan road | Open both ends | skip only |

First crossing of every route is always played (it is part of the wonder of arrival). After that the player may skip. NPC ships and caravans run the same routes abstractly (tier T3, section 5.5), so goods flow even when the player is elsewhere.

---

## 4. Survival without violence

Pressure comes from nature and logistics, never from enemies. Every pressure has a visible cue before it bites.

| Pressure | Meter / rule | Cue | Effect when low | Fix |
|---|---|---|---|---|
| Cold | Warmth 0-100. Drops in wind, rain, snow, water, night; rises near fire, indoors, in good clothes | Breath fog, shivering idle, frost vignette at < 30 | < 30: run speed x0.85, climb speed x0.8. At 0: "chilled", see setback | Fire, shelter, clothing, hot food, hot springs |
| Hunger | Fullness 0-100, -4 per in-game hour awake (my call) | Stomach rumble, slower idle | < 25: stamina regen x0.5 | Eat (cooked food gives more and a short warm buff) |
| Rest | Rest 0-100, -3 per in-game hour awake | Yawns, slower camera sway | < 20: sprint disabled | Sleep in a bed (full), a bedroll (75%), sit at a fire (slow) |
| Night | Real darkness 20:00-06:00, moonlit; caves are dark | Dusk light, lanterns lit in town | Hard to see paths and resources | Lantern, torch, campfire, moon phases |
| Terrain | Stamina 0-100 for sprint, climb, swim | Breathing sounds, stamina ring near the character | At 0 on a wall: hang, then slide down to the nearest ledge. At 0 in water: slow float to shore | Rest, food, better boots/gloves |
| Carry weight | Backpack 30 kg; basket +15, handcart 120, pack pony 150, boat 800 (my call) | Weight bar on the bag icon, posture changes | Over limit: walk only, no climb, no jump | Drop, stash, cart, pony, warehouse |
| Weather | Rain, storms, fog, snow, heat (R3) | Sky, wind sound, barometer item | Slower boats, closed passes, wet = colder | Wait, shelter, plan |

**Setback instead of death.** When Warmth hits 0, or the player sits at Fullness 0 and Rest 0 together, the screen fades and the player wakes at the nearest bed or campfire they own or rent, at the next 06:00. Cost by preset:

| Preset | Meter drain | Setback cost | Climbing stamina | Default for |
|---|---|---|---|---|
| **Gentle** | x0.5 | None. Nothing lost. | Climbing never drains (my call) | Youth, first launch |
| **Wayfarer** | x1.0 | Perishable food in the bag spoils; half a day passes | Drains, regen on ledges | Most players |
| **Hardy** | x1.5 | Perishables lost, 10% of carried goods left where you collapsed (marked, recoverable) | Drains faster, no regen on wall | Adults wanting tension |

All presets are switchable at any time in settings (no lock-in). Falls never hurt: drops above 6 m end in a heavy-landing roll and 2 s of stagger; drops above 15 m are only possible into deep water (an authored "Wayfarer's dive" spot) or are blocked by auto-ledge-catch (section 7).

---

## 5. Systems spec

All content is data: `NpcDef`, `ItemDef`, `ResourceDef`, `BuildingDef`, `BiomeDef`, `RegionDef`, `TradeRouteDef`, `WorldEventDef`, `RumorDef`, `WonderDef`, `DialogueTemplateDef`, `QuestDef`. No per-NPC or per-place code (feedback). The sim runs on a fixed tick, decoupled from the frame rate, and is deterministic from a seed (needed for the automated playthrough test and the stress ladder).

### 5.1 World simulation clock
| Tick | Rate | What runs |
|---|---|---|
| Frame | 30/60 Hz | Player, camera, T0 NPC animation |
| Sim tick | 5 Hz | T0 NPC decisions, interactions |
| Hour tick | every in-game hour (60 real s) | Weather step, river level, resource regrowth, production, T2 NPC schedules |
| Day tick | 06:00 | Market prices, stock consumption, rumor decay and spread, settlement growth check, route arrivals, T3 regions |

### 5.2 Worked simulation chains

**Chain A: rain -> river -> fish -> prices -> people -> opportunity** (feedback)
1. Weather rolls a 3-day front (on average 1 heavy front per 6 days, my call). Each rain-hour raises the river 0.3 m, capped at +1.5 m; it falls 0.2 m per dry hour.
2. River +1 m or more: boat speed on the river x0.75 (my call: `x(1 - 0.25 * level/1.5)`), ford crossing closed, the lower dock floods.
3. Muddy water: fish catch x0.3 while the flood lasts.
4. Fresh fish stock falls 85 -> 58 -> 32 -> 6 over 3 flood days; price goes 4.8 -> 6.0 -> 8.7 -> 15.0 (cap at 3x base) (my calc, section 5.3 formula).
5. Fishers change schedule: they mend nets at home instead of rowing out (Social need rises, they spend more time at the longhouse, more rumors shared).
6. The visiting trader's boat is delayed 1 day (slower river), so no outside fish arrives.
7. Player opportunity: smoked fish made earlier sells high; the upstream lake (clear water, unaffected) still fishes well; or help Ingrid fix the flooded dock (+ village and craft reputation).

**Chain B: cold snap -> firewood -> timber -> work and mood**
1. A cold snap (Hardy autumn/winter, or a "cold night" event on any preset) doubles household firewood use for 2 days.
2. Pine log stock falls; price rises from 4.0 toward 6.1 at half stock (my calc).
3. Woodcutters extend work shifts by 2 h; their Social need goes unmet, mood -10, they are short with the player in dialogue (a "tired" line set).
4. Houses without a woodshed burn through stock first; their residents gather at the longhouse fire (crowded evening scene).
5. Player opportunity: sell split firewood, build a woodshed for a household (that household is warm from then on and remembers it), or fetch birch bark (fire starter) for the elder.

**Chain C: player builds a bridge -> route -> prices -> growth**
1. Player completes the stone footbridge over the gorge (BuildingDef `bridge_stone`).
2. Walking time farm -> market drops from 6 to 2 real minutes; NPC farmers' schedules move 1 hour earlier to market.
3. Farm goods (wool, flax) reach the stall every day instead of every other day: stock evens out, price swings shrink by about half (my call).
4. The trader's route adds a stop: imports (salt, grain) arrive at the stall, salt price falls from 9 to 6.
5. Cheaper salt -> fishers smoke and salt more fish -> fish exports rise -> village Prosperity +5 -> one step closer to growth (5.10).
6. Rumors about "the old gorge path" become **outdated** automatically (5.6).

**Chain D: wonder found -> material -> festival**
1. Player reaches the Singing Cavern and harvests 3 resonant crystals (only the first visit yields crystal; later visits give 1 per in-game week).
2. The smith (if relationship Trusted) can cast a village bell with crystal + 20 bog iron + 10 clay.
3. Bell installed -> the village holds its first Lantern Festival 2 days later; demand for honey, berries and smoked fish x2 for that day; NPCs gather on the green; visitors from the trader boat stay; rumor spread rate x2 that night.

### 5.3 Economy

Price formula (my call), per market, recomputed at each day tick and after each player trade:

```
target_stock = daily_consumption * days_of_cover
price = base * clamp((target_stock / max(stock, 1)) ^ 0.6, 0.4, 3.0)
buy_price  = price * 1.10   (what the player pays)
sell_price = price * 0.90   (what the player gets)
```
Exponent 0.6 keeps one big sale from crashing a price; the clamp keeps every good between 40% and 300% of base. Selling 20 fish into a balanced market moves the fish price from 5.0 to 4.4 (my calc), so dumping is possible but not free.

Each market keeps per-good `stock`, `daily_production` (sum of working NPC producers and buildings), `daily_consumption` (residents x needs + building inputs), and `days_of_cover` (perishables low, durables high). Trade routes move goods from the market where the price is lowest to where it is highest, limited by capacity and trip time.

**Slice 01 starting price table** (Skarvik market, coins; my calc from the formula above)

| Resource | Base | Prod/day | Cons/day | Days of cover | Target stock | Price at 50% stock | At 100% | At 200% |
|---|---|---|---|---|---|---|---|---|
| Pine log | 4 | 60 | 50 | 5 | 250 | 6.1 | 4.0 | 2.6 |
| Granite block | 6 | 20 | 15 | 7 | 105 | 9.1 | 6.0 | 4.0 |
| Fresh fish | 5 | 45 | 40 | 2 | 80 | 7.6 | 5.0 | 3.3 |
| Cloudberries | 8 | 12 | 10 | 3 | 30 | 12.1 | 8.0 | 5.3 |
| Raw wool | 7 | 15 | 12 | 7 | 84 | 10.6 | 7.0 | 4.6 |
| Flax | 5 | 18 | 15 | 7 | 105 | 7.6 | 5.0 | 3.3 |
| Clay | 3 | 25 | 20 | 7 | 140 | 4.5 | 3.0 | 2.0 |
| Bog iron ore | 12 | 6 | 5 | 10 | 50 | 18.2 | 12.0 | 7.9 |
| Birch bark | 2 | 30 | 20 | 5 | 100 | 3.0 | 2.0 | 1.3 |
| Wild honey | 14 | 3 | 3 | 7 | 21 | 21.2 | 14.0 | 9.2 |

Production slightly exceeds consumption for most goods so stock grows slowly without events; events, festivals and the player pull it back. Imports in the slice (salt, grain) enter via the single trade route at base 9 and 6.

**Slice 01 items (processed)**

| Item | Recipe | Station | Time (in-game) | Base value |
|---|---|---|---|---|
| Planks (x4) | 1 pine log | Sawhorse / workshop | 20 min | 2.0 each |
| Cut stone | 1 granite block | Mason's bench | 30 min | 9 |
| Smoked fish | 2 fresh fish + 1 birch bark | Smokehouse | 4 h (unattended) | 13 |
| Berry preserve | 4 cloudberries + 1 honey | Kitchen | 30 min | 40 |
| Yarn | 2 raw wool | Spindle | 40 min | 16 |
| Linen cloth | 3 flax | Loom | 2 h | 18 |
| Brick (x2) | 1 clay + fire | Kiln | 3 h (unattended) | 3.5 each |
| Iron nails (x10) | 1 bog iron ore + charcoal | Smithy (NPC smith or player at Trusted) | 1 h | 1.6 each |
| Rope | 3 birch bark | Hand (anywhere) | 15 min | 7 |
| Firewood bundle | 1 pine log | Chopping block | 10 min | 5 |

Processing adds 20-60% value (my call): enough to reward a stop at a station, not enough to make raw selling pointless.

### 5.4 NPC layers

**Layer 1: needs, schedule, goals (deterministic game AI)**

| Need | 0-100 | Decays per in-game hour | Satisfied by |
|---|---|---|---|
| Hunger | | 5 awake, 1 asleep | Eating at home, longhouse, stall |
| Energy | | 4 awake | Sleep, sit |
| Social | | 3 | Talking with NPCs or the player, longhouse, festival |
| Safety/comfort | | 2 in bad weather, 0 otherwise | Shelter, warmth, home |

Schedule (archetype template, shifted by personality): wake 05:30-07:00, work blocks, meals 07:00/12:00/18:00, socialize 18:30-21:00, sleep. A need below 25 interrupts the schedule with the matching action (utility scoring: pick the highest `need_urgency * weight` among available actions, my call).

**Layer 2: personality, preferences, relationships (data)**

```
NpcDef {
  id, name, archetype, voice_id, home_id, work_id,
  personality { warmth 0-1, chattiness 0-1, thrift 0-1, curiosity 0-1, routine 0-1 },
  likes [item/topic ids], dislikes [...],
  skills { fishing, woodwork, ... 0-100 },
  relationships { npc_id or "player": { affinity -100..100, trust 0..100 } },
  memories [Memory]   // see schema
}
```

**Layer 3: dialogue expresses facts, never invents them.** A line is only eligible if every slot it uses is filled from live sim state (section 6).

**Semantic memory schema** (feedback: events, not transcripts)

```
Memory {
  id, subject ("player" | npc_id | place_id),
  event_type   // helped, traded_fair, traded_hard, gave_gift, built_for_me,
               // absent_long, witnessed_wonder_story, shared_rumor, rescued_goods, ...
  object_id    // item / building / rumor involved, may be null
  importance   // 1-10
  affinity_delta, trust_delta,
  day, place_id,
  told_count   // how often the NPC has mentioned it (stops repeats)
}
```
Cap 32 memories per NPC; when full, drop the lowest `importance - days_old/7`. Importance >= 8 never drops (a house you built them). `absent_long` is written when the player has not spoken to an NPC with affinity >= 40 for 7 in-game days.

### 5.5 NPC LOD tiers

| Tier | Range (from player) | AI update | Animation | Representation |
|---|---|---|---|---|
| T0 Full | < 40 m (max 12 high-end / 6 floor) | Decisions 5 Hz, path every move | Full skeleton, IK feet, look-at, lip flap | Full mesh, LOD0-1 |
| T1 Near | 40-150 m | 1 Hz, coarse paths on the nav graph | Reduced bones, 15 Hz animation, no IK | LOD2 mesh |
| T2 Far | 150 m - 2 km (same region) | Every 10 s: schedule slot -> position on the town graph | None | Impostor billboard or hidden |
| T3 Abstract | Other regions | Once per in-game hour, aggregated per settlement | None | Counters only: population, needs met %, production |

Promotion T2 -> T1 -> T0 snaps the NPC to the right place in their schedule (where they would be now), so a player never sees someone teleport into view. Promotion is capped at 2 NPCs per frame to avoid spikes.

### 5.6 Rumors

| Truth state | Meaning | Example |
|---|---|---|
| True | Matches the world | "There's singing behind Bluewater Falls at dawn." |
| Partly true | Right place, wrong detail | "...singing behind the falls at midnight." (dawn only) |
| Outdated | Was true, the world changed | "The gorge path is the only way to the farm." (player built the bridge) |
| Exaggerated | Right fact, wrong size | "The whale bones on the beach are taller than the longhouse." (they are half that) |
| False | Never true | "Old Bror buried silver under the boathouse." |

```
RumorDef { id, region, subject_place/item/npc, truth_state, variants[state -> line ids],
           invalidated_by [world fact], reward_hint (wonder_id, resource_id, price_tip) }
RumorInstance { rumor_id, holder_npc, confidence 0-1, hops, day_heard, state }
```
Rules (my call): when two NPCs socialize, 30% chance one shares a rumor with confidence >= 0.3. Each hop: confidence x0.85, and 10% chance the state drifts one step (true -> partly true or exaggerated). Confidence -0.05 per day; below 0.15 the NPC forgets it. If a world fact in `invalidated_by` changes, every instance flips to Outdated. All rumor text is authored and voiced ahead of time per state, so drift picks another pre-voiced line, never new text. The journal stores who told the player what and when, unverified until the player sees the place.

Slice 01: 12 rumors (4 true, 2 partly true, 2 outdated-able, 2 exaggerated, 2 false); 3 of them point toward the Singing Cavern.

### 5.7 Reputation tracks
0-100 each, bands: Stranger 0-19, Known 20-39, Trusted 40-59, Valued 60-79, Kin 80-100. No good/evil axis (feedback).

| Track | Scope | Gains | What it unlocks |
|---|---|---|---|
| Village | per settlement | Help, fair trade (+0.5), buildings (+5 to +15), festivals | Housing plots, warehouse, council voice, cheaper rent |
| Merchant | per trading house / trader NPC | Volume traded, delivered contracts on time | Better buy/sell spread (to 5%/5% at Valued), route contracts, credit |
| Craft | per craft: woodwork, stonework, textiles, cooking, smithing, boatbuilding | Items crafted and sold, quality | Recipes, stations, apprentices |
| Explorer (Wayfinder) | global | Wonders found, routes opened, rumors verified | Map details, guide offers, rumor quality (more true rumors) |
| Community | per community group (fishers, herders, ruin-keepers...) | Living up to their values (help in floods, attend festivals) | Their homes, their festivals, their secrets |

Decay (my call): above 40, -1 per 7 in-game days of absence, never below the band floor you reached (Trusted stays Trusted). NPCs still remark on absences through memory lines.

### 5.8 Building

| Stage | Needs (house example) | What changes in the sim |
|---|---|---|
| 0 Plot | Village reputation Known, plot marker | Path rerouted around the site; NPCs comment |
| 1 Foundation | 12 cut stone | Site becomes walkable platform; workers may help if paid |
| 2 Frame | 20 planks, 40 nails | Silhouette visible from afar |
| 3 Walls | 30 planks, 10 rope (or 30 bricks) | Shelter: counts as wind cover |
| 4 Roof | 20 planks + 20 birch bark + turf (gathered) | Counts as warm shelter; can sleep here (player) |
| 5 Finished | Door, hearth (10 bricks) | Adds housing capacity 3; triggers move-in check |
| 6 Occupied | Household arrives within 1 in-game day if growth conditions hold | New NPCs, new production, new consumption, new dialogue |

Slice 01 buildings: house, woodshed, smokehouse, market stall extension, stone footbridge. Each finished building changes at least one number in the sim (housing, warmth, production rate, stock capacity, travel time). Player helpers: NPCs with affinity >= 40 may join a stage for coins or goods (halves the time).

### 5.9 Wonders
Target: **30 major wonders** (6 per region) + **8 timed events** (northern lights, meteor shower, spring flower bloom, autumn larch gold, bioluminescent tide, frozen falls, double rainbow after storms, solar halo). Most are not on the map until a rumor, a view from a high point, or a found object points to them.

Discovery rewards (no combat loot):
| Reward | Example |
|---|---|
| A vista + journal lore page with an illustration | Singing Cavern: why it sings (wind through crystal pipes) |
| Wayfinder reputation +10 (major) / +3 (event) | |
| A unique material with a community use | Resonant crystal -> village bell -> festival |
| A cairn: fast travel point to here | |
| A new rumor chain toward the next wonder | Crystal's maker's mark -> "the old observatory" rumor in R2 |

Slice 01: 1 mysterious location (Singing Cavern behind Bluewater Falls) + 1 timed event (northern lights on clear nights, about 1 in 4).

### 5.10 Settlement growth

| Stage | Population | Required buildings | Other conditions | New on reaching it |
|---|---|---|---|---|
| Hamlet | 1-24 | Longhouse, homes | - | Start of slice (20 residents) |
| Village | 25-59 (e.g. 43) | Market stall, 1 workshop | Food cover >= 5 days, Prosperity >= 30 | Weekly market day, trader calls every 3 days |
| Market village | 60-119 (e.g. 71) | Dock, warehouse | Prosperity >= 50, one active trade route | Second stall, inn, sea route |
| Town | 120-249 (e.g. 132) | Guildhall, 2 crafts at Valued | Prosperity >= 65, 2 routes | Guild contracts, seasonal festival |
| Port town | 250+ | Harbour, 3 routes | Prosperity >= 75 | Shipyard, region-wide events |

Growth rule (my call): at the day tick, if free housing > 0, food cover >= 5 days and average mood >= 50, one household (2-3 people) arrives. Players drive growth by building homes; the village never shrinks below its stage floor (no punishment for leaving). Slice 01 target: 2 houses built -> 25-26 residents -> Village.

Prosperity 0-100 = weighted average of food cover, housing slack, mood, trade volume (my call: 30/20/30/20).

---

## 6. Dialogue and voice pipeline

No live LLM, all offline (owner). Text and audio exist at build time.

### 6.1 Data flow
```
Simulation facts (WorldState, NPC needs/memories/rumors/reputation)
    -> DialogueTemplateDef  (dev time, written by designers)
         id, archetype, topic, conditions[], slots[] with closed value sets, weight
    -> Claude-authored variants (dev time)
         for every template x archetype x personality band x slot value:
         2-4 phrasings, reviewed by a human, stored as text with stable line ids
    -> Local TTS render (build time, per NPC voice_id)
         one audio file per (line id, voice); loudness-normalized; reviewed by ear
    -> Cached audio in asset packs (Opus mono, 24 kbps)
    -> Runtime selector (no LLM): pick an eligible line by conditions + score, play its clip
```

Slots must have closed value sets so every combination is voiced ahead of time. Example: `{resource}` limited to the NPC's 3 trade goods, `{price_state}` in {cheap, normal, dear}. A template may expand to at most 24 voiced variants per voice (my call), or it must be split.

### 6.2 Runtime selection (deterministic)
1. Collect templates for the NPC's archetype and the current trigger (greet, idle bark, trade, ask about, farewell, react to event).
2. Drop any whose conditions fail (relationship band, time, weather, memory exists, rumor held, price state, building state).
3. Score = base weight + 3 if it uses an unmentioned memory with importance >= 6 + 2 if it uses a rumor the player has not heard + 1 per personality match - 5 if spoken to the player in the last 2 days.
4. Pick the highest (ties: seeded random). Increment the memory's `told_count`.

### 6.3 Line budget, slice 01 (my calc)
| Category | Lines per NPC |
|---|---|
| Greetings (5 relationship bands x 4) | 20 |
| Farewells | 10 |
| Work/schedule barks | 15 |
| Need barks (hungry, tired, cold, lonely) | 10 |
| Weather and season | 12 |
| Market and prices (3 goods x 3 states x 2) | 18 |
| Memory callbacks (help, trade, absence, gift, built) | 20 |
| Rumor tellings (state variants) | 12 |
| Requests and thanks | 15 |
| Building and settlement reactions | 10 |
| Wonder reactions | 6 |
| **Total** | **148** |

8 archetypes in the slice (fisher, woodcutter, farmer, smith, trader, innkeeper, elder, child). 20 NPCs x 148 = 2,960 voiced clips, about 28 MB at 24 kbps and 3.2 s average (my calc). Full game estimate: 5 regions x 60 NPCs x 180 lines = 54,000 clips, about 506 MB (my calc): needs on-demand asset packs per region (ask).

### 6.4 Example: Ingrid, fisher (warmth 0.6, chattiness 0.4, thrift 0.8)
| Relationship / memory | Line |
|---|---|
| Stranger, no memory | "You're not from the fjord. Mind the nets on the rocks." |
| Known, `traded_fair` (fish) | "You paid a fair price for my herring last week. I don't forget that." |
| Trusted, river flood (live fact: river +1.2 m) | "River's brown as tea. No fish today. If you've any smoked put by, the stall will pay well." |
| Trusted, `absent_long` | "Seven days and not a word. I thought the sea had kept you." |
| Valued, `built_for_me` (smokehouse) | "The smokehouse you built has fed my family through the whole flood. Sit, eat with us." |
| Kin, rumor held (Singing Cavern, true) | "My grandmother swore the falls sing at first light. I never had the nerve to look behind them. You would." |

---

## 7. Controls (phone, landscape 1920x1080)

Touch targets: minimum 130 px hit area (48 dp, studio rule); primary buttons drawn 170-190 px. All controls sit inside the display safe area; hit areas extend to screen edges.

| Zone / control | Where | Behaviour |
|---|---|---|
| Move stick (left thumb) | Floating, anywhere in x 0-800, y 300-1080 | Base appears under the thumb, dia 260 px, knob 120. Dead zone 12%. Walk below 70% deflection, jog above. Release = decelerate (section 8 numbers). |
| Camera (right thumb) | Drag anywhere in x 800-1920 not on a button | Yaw 0.22 deg/px, pitch 0.15 deg/px, pitch clamp -35..+60 deg, sensitivity slider 0.5-2x. After 2 s without drag while moving, camera eases behind the player over 0.8 s. |
| **Action** (context) | Circle dia 190, centre (1700, 860) | Icon shows what it does: Gather, Talk, Pick up, Place, Open, Sit, Sleep, Build, Board. Tap = do it. Hold = repeat (harvest a whole bush, carry on). |
| **Traverse** (hold) | Circle dia 170, centre (1480, 960) | Hold + move = run and free-run: vault low walls, climb ledges, swing on beams, climb walls, all automatic in the stick's direction (Assassin's Creed style). Release on a wall = hang and stay. Tap while running toward a gap or edge = jump. |
| Drop / Let go | Circle dia 140, centre (1760, 640), only visible when carrying, climbing, sitting or swimming | Carrying: put down. Climbing: let go to drop to the ledge below (safe drop only). Swimming: dive (P2). |
| Bag, Map, Journal | Top right, 3 icons dia 130, y 90 | Open full-screen panels; game pauses (my call). |
| Meters | Top left, small | Warmth, Fullness, Rest only when below 50; stamina ring around the character, not the HUD. |

Climbing feel: holds are authored (ledges, beams, cracks, ropes, carved steps) and read naturally, with a light dust-wash on climbable rock instead of yellow paint (graphic-designer to confirm). Climb speed 1.0 m/s vertical, 1.4 m/s with Traverse held; a 2 m ledge is mantled in 0.9 s. Holding the stick toward a wall with Traverse held starts climbing; holding away + tapping Traverse jumps backward to the next hold if one exists within 2.5 m, else nothing. The game never jumps the player off a cliff: an edge with no safe landing stops the player with a short balance wobble (0.4 s).

---

## 8. Movement and animation list

Speeds (my call): walk 1.6 m/s, jog 3.6, run (Traverse) 5.8, swim 1.4, swim fast 2.2, carry heavy x0.6. Acceleration 0 -> jog in 0.25 s, jog -> stop in 0.3 s with a settle step; turn in place above 120 deg plays a pivot.

| Tier | Movements and animations |
|---|---|
| **P0 (slice must have)** | Idle (3 variants), walk, jog, run with start/stop/pivot, slope lean, stairs up/down, jump (standing, running), land (soft, heavy roll), climb wall (4 directions), mantle low/high, ledge hang + shimmy, vault, swim surface + enter/exit water, pick up from ground, harvest (bush, tree chop, stone mine), carry crate (two-handed), place object, talk (idle + 3 gestures), sit (bench, ground), sleep (lie down / wake), NPC: walk, work loops for 8 archetypes, eat, talk pairs |
| **P1 (slice nice to have, beta must)** | Balance beam walk, rope climb, ladder, crouch through gaps, push handcart, row boat, fish (cast, reel), hammer/build, cook at fire, wave/point/shrug/laugh emotes, shiver/yawn/wipe-brow survival idles, wind lean, wade in shallow water |
| **P2 (beta and later)** | Dive underwater, sail trim/steer, ride pony, lead pack animal, slide down scree, zipline/rope slide, dance (festival), hug/handshake pairs, child NPC play loops, animal-specific interactions (pet, feed) |

---

## 9. Vertical Slice 01: one valley

### 9.1 Scope
Skarvik valley, about 2x2 km: 1 hamlet (20 NPCs, 8 archetypes), forest, river with falls, a mountain to climb, 10 resources, 10 items, 5 buildings, 1 market, 1 trade route (trader boat every 3 days, abstract origin), weather, day/night, 1 mysterious location (Singing Cavern), northern lights event, save/load. Actions: walk, run, jump, climb, swim, gather, craft, build, sell, buy, talk, explore, sleep, save.

### 9.2 Acceptance criteria
Every block also has an automated playthrough step (seeded bot, headless where possible).

**Movement**
- [ ] Walk/jog/run with acceleration and stop settle; no foot sliding visible at 60 fps capture.
- [ ] Climb the marked cliff (40 m) from base to top using only Traverse + stick, in under 70 s.
- [ ] No position on the map lets the player fall more than 15 m except the dive spot.
- [ ] Swim across the river and exit on the far bank without getting stuck (bot: 20 random crossings).

**Gather, craft, carry**
- [ ] All 10 resources gatherable; each regrows on its timer (berries 3 days, trees 7 days, ore 5 days, my call).
- [ ] All 10 recipes craft at their station and show progress.
- [ ] Over-weight blocks climbing and running and shows why.

**Economy**
- [ ] Prices follow the 5.3 formula within 0.1 coin (unit test against the table).
- [ ] Selling 20 fresh fish into a balanced market lowers the price to 4.4 +-0.1.
- [ ] A forced 3-day flood raises fish price above 12 by day 3 (Chain A).
- [ ] Trader boat arrives every 3 days, delayed 1 day when the river is above +1 m.

**NPCs**
- [ ] 20 NPCs follow schedules; at 22:00, 18 or more are home or asleep.
- [ ] Needs interrupt schedules (force Hunger 10: NPC eats within 1 in-game hour).
- [ ] Memory written for help, trade, gift, build, absence; the next greeting uses it (bot check of line id).
- [ ] LOD promotion never shows an NPC popping into view within 40 m.

**Dialogue and voice**
- [ ] Every voiced clip plays for its line id; 0 missing clips (build-time check).
- [ ] No line plays whose slots contradict live state (fuzz test: 10,000 random states).
- [ ] Same line not repeated to the player within 2 in-game days.

**Rumors and wonder**
- [ ] 12 rumors spread; at least 3 reach the player in a 3-day bot run.
- [ ] Building the footbridge flips the gorge-path rumor to Outdated.
- [ ] Singing Cavern is reachable only by climbing behind the falls; first visit gives 3 crystals and a journal page.

**Building and growth**
- [ ] All 5 buildings pass all stages; each finished building changes its sim number (housing, warmth, travel time...).
- [ ] Building 2 houses grows the hamlet to 25+ and to Village stage; market day starts.

**Survival**
- [ ] Gentle: a full night outside in rain causes no setback. Hardy: it does, and the player wakes at the nearest bed with the correct losses.
- [ ] Preset can be changed mid-game with no reload.

**World**
- [ ] Day/night cycle 24 real min; weather fronts change light, sound, river level.
- [ ] Northern lights show on at least 1 of 4 clear nights (seeded check).
- [ ] Save anywhere, load restores sim state exactly (hash compare of WorldState).

### 9.3 NPC stress-test ladder
Run on the floor device and the high-end device, 10 real minutes each, player walking a fixed loop through the hamlet.

| Step | Sim NPCs | T0 cap | Pass |
|---|---|---|---|
| 1 | 20 | 12 / 6 | p95 frame <= 16.7 ms high / 33.3 ms floor; sim tick <= 1.0 ms |
| 2 | 50 | 12 / 6 | same, sim tick <= 1.5 ms |
| 3 | 100 | 12 / 6 | same, sim tick <= 2.0 ms; no GC spike > 4 ms |
| 4 | 250 | 12 / 6 | p95 holds; RAM +<= 60 MB over step 1 |
| 5 | 500 | 12 / 6 | p95 holds; save file <= 2 MB; save time <= 300 ms |

If a step fails, the fix order is: lower T1 radius, then T1 rate, then T0 cap; never cut needs or memory.

### 9.4 Performance budget (my call, confirm devices: ask)
| Metric | High-end (60 fps) | Floor (30 fps) |
|---|---|---|
| Frame time p95 | 16.7 ms | 33.3 ms |
| Draw calls | <= 200 | <= 120 |
| Triangles on screen | <= 800k | <= 350k |
| Full (T0) skinned NPCs on screen | 12 | 6 |
| Sim CPU per frame (avg) | <= 2 ms | <= 3 ms |
| RAM total | <= 1.6 GB | <= 1.0 GB |
| Base install | <= 150 MB, voice + region art as asset packs | same |
| Thermal | 30 min session holds >= 50 fps | 30 min holds 30 fps |
| Battery | <= 15% per 30 min | <= 15% per 30 min |
| Shader compile hitch | none after first launch (precompile at boot) | same |

---

## 10. Roadmap

| Milestone | Content | What it proves |
|---|---|---|
| **Slice 01** | One valley (R1 Skarvik), section 9 | Movement feels good on a phone; the sim chains are readable to a player; pre-voiced reactive dialogue feels alive; the budget holds at 20-500 NPCs; the engine choice was right |
| **Slice 02** | R2 Amberline Isles (1 island town, 30 NPCs) + the sea route + boat building + sailing crossing | Two economies with different shortages make trade worth doing; T3 abstract region stays in sync when the player returns; region asset packs stream on a phone; travel feels like part of the game, not a loading screen |
| **Beta** | R1-R5 at first-pass depth, 30 wonders, 8 events, 4 trade routes, settlement stages up to Town, all P1 animations | The week loop holds for 20+ hours; full voice budget fits; the youth preset is calm and the Hardy preset has tension; Play Store asset-pack delivery works |

---

## 11. Name candidates
Working titles only. **I did not run a trademark or store-name check** on any of them.

1. Hearthroads
2. Far Harbours
3. Tidewright
4. The Wonder Roads
5. Saltwind Crossing
6. Lanterns of the Long Coast

---

## 12. My calculations
Script: `tools/econ_calc.py` (run `python3 tools/econ_calc.py`; its NPC-cost lines are placeholders, ignore them). Formula in 5.3. Flood run: fish stock 80 target, consumption 40/day, catch x0.3 for 3 days -> stock 85, 58, 32, 6 and price 4.8, 6.0, 8.7, 15.0 (capped). Audio: clips x 3.2 s x 24 kbps / 8. Growth pace: 1 household per day when conditions hold.

---

## 13. Open questions for the owner
1. **Youth age band**: 10-15 (my guess) or younger? It sets reading level, preset defaults and Play Store rating.
2. **Target devices**: which phone is the 60 fps high-end and which is the 30 fps floor? Budgets in 9.4 are guesses until then.
3. **Voice quality bar**: is local English TTS acceptable for 20 NPC voices, or do key characters need recorded human voices? (For the Norwegian reading game you rejected free TTS.)
4. **Full-game size**: about 506 MB of voice for the full game (my calc). OK as downloadable region packs, or cut lines per NPC?
5. **Survival default**: Gentle or Wayfarer on first launch?
6. **Time scale**: is 24 real minutes per in-game day right, or longer (Skyrim-like ~72 min)?
7. **Slice region**: confirm the slice is the Nordic fjord (R1).
8. **Sailing**: hand-sailed crossings (more work, more wonder) or a ride-along cutscene with free camera?
9. **Character creation**: one fixed protagonist, or pick body/face/voice? Affects voice lines (NPCs say a name?).
10. **Pause on menus**: should the world pause while the bag/map is open (my call: yes)?
