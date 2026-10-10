# MWM Wayfarer (working title): game design doc

Version 2, 2026-10-10, game-designer. Slug `mwm-wayfarer`. Engine: Godot 4.6 Mobile (owner 10-10, phone spike live). v1 (552 lines, five trade regions) is archived unchanged at `docs/archive/GDD-v1-2026-10-10.md`; v2 keeps its systems and rebuilds the structure around the owner's new vision of 2026-10-10.

Target: Android, landscape 1920x1080, third person, realistic high-end look (owner; art spec in `docs/DESIGN.md`). Fully offline, no ads, no tracking, no live LLM.

Legend: **(owner)** = owner decision, do not reopen. **(my calc)** = my own arithmetic (`tools/fire_calc.py`, `tools/econ_calc.py`). **(my call)** = a design choice I made, change freely. **(ask)** = open question, section 17. **(checked)** = a fact I checked in a web source this session (list in section 16). **(unverified)** = a date or fact from my own knowledge, not checked; it must be checked before it ships in game text. **(invented)** = in-world fiction made up for the game, not a real tradition.

---

## 1. Pitch, pillars, players

### 1.1 Pitch
Follow one human line through the whole human story: from the first apes to come down from the trees and walk on the ground in Africa, through fire, words, the Ice Age and the first boats, to a fjord farm in the 1800s and the same fjord today. Come back to the same real places in different ages, find what you left there long ago, and learn which legends began with something you saw.

### 1.2 Design pillars
| # | Pillar | Test a feature must pass |
|---|---|---|
| P1 | **The world runs without you** | Does the fact come from the simulation (weather, stock, schedule, memory, season) rather than a script? (v1) |
| P2 | **Movement is a pleasure** | Is walking, climbing a tree or cliff, or swimming satisfying with no goal? (v1) |
| P3 | **Wonder is earned by curiosity** | Does the player find it by listening, looking and going, not by a quest marker? (v1) |
| P4 | **You matter by making and sharing** | Does the player's work visibly change a place: fire, food, buildings, people, routes, prices? (v1, widened for eras without money) |
| P5 | **Time leaves traces** (owner 23:24) | Does something the player did or saw in one era show up, changed, in a later era? |

### 1.3 Target players
Unchanged from v1: youth (age band still open, ask) and adults; calm 15-40 minute phone sessions; Gentle / Wayfarer / Hardy presets.

### 1.4 What the game deliberately does not have
- No combat. The player never attacks a person or an animal. Animals graze, flee, follow, watch or ignore you. Predators create pressure (they come near a camp without fire), never damage. (v1, owner: no violence as core)
- **Hunting** (owner asked for it in early eras) happens as a group activity the player supports: tracking, reading signs, driving a herd toward the hunters, signalling. The kill is never shown and never player-controlled; the scene cuts to the hunters coming home. Fishing, trapping and gathering are shown in full. (my call, ask)
- No death, no health bar. Cold, hunger, tiredness, deep water and night predators cause setbacks, never game over. (v1)
- Ageing and the passing of generations happen off screen, as a handing-over scene (section 4.3). Plague and war exist only as history told in lore and seen in their traces (empty farms, a burnt hall), never as scenes. (my call)
- No crime loop, no loot drops, no character levels, no energy timers, no ads, no premium currency. (v1, studio)
- No live text generation. Every spoken line and every call exists at build time. (owner)

---

## 2. Structure: eras, anchor places, chapters

### 2.1 Three layers
| Layer | What it is | Count |
|---|---|---|
| **Era** | One period of human history with its own character, actions, tools, speech and economy | 12 |
| **Anchor place** (owner 23:24) | One real terrain (same DEM) that the player visits in several eras, changed by time | 4 core + 1 optional |
| **Chapter** | What we build and ship: one era at one or two places | 1 chapter per era; some eras have two acts |

The player plays the eras in order. After an era is finished it stays open on the **Long Map** (section 4.4): any finished era at any anchor can be revisited.

### 2.2 Era table
Dates marked (checked) come from the sources in section 16; all others are (unverified) until checked.

| # | Era (working name) | When | Anchor / place | You are | Key discovery that unlocks the next era |
|---|---|---|---|---|---|
| 1 | **From the trees to the ground** | ~7 to ~3.3 million years ago (earliest upright walkers ~7-4 Mya, unverified; first stone tools 3.3 Mya, checked) | A2 Rift lake (West Turkana, Kenya) | A young ape-like hominin in a band of ~14 | **The stone that cuts** (Lomekwian flake, 3.3 Mya, checked) |
| 2 | **Keepers of the fire** | ~1.9 to ~0.8 Mya (Homo erectus span unverified; controlled fire ~1 Mya at Wonderwerk, checked, debated) | A2 Rift lake, a drier age | A Homo erectus youth, long-legged walker | **Fire kept alive**: carry, feed and guard fire; sleep on the ground |
| 3 | **Words by the sea** | ~100,000 to ~60,000 years ago (shell beads and engraved ochre at Blombos ~75,000 years, checked) | A3 Southern Cape coast cave (Blombos-like); act 2: the walk north (desert canyon) | A Homo sapiens youth | **Words and signs**: language, ochre marks, gift beads; then the walk out of Africa (~70-50k years ago, unverified) |
| 4 | **Painted caves** | ~20,000 to ~15,000 years ago (unverified) | A4 Vezere cave valley (Dordogne, France) | An Ice Age hunter-gatherer teen | **Sewn clothing + the dog**: you can follow the reindeer north as the ice melts |
| 5 | **After the ice** | ~9500 to ~8000 BC (first coastal settlers of Norway, checked) | **A1 Naeroyfjord** (Skarvik), ice on the heights | A pioneer in a small family band arriving by skin boat | **The boat and the coast road** (and making fire anywhere with flint and pyrite) |
| 6 | **First fields** | ~4000 to ~2350 BC (Funnel Beaker ~4000 BC; farming economically important from ~2450-2350 BC, checked) | A5 Jaeren coast (optional anchor) or A1 | A child of the first farming households | **Farming and pottery**: a settled home |
| 7 | **Bronze and iron** | ~1700 BC to ~AD 750 (unverified) | A5 Jaeren (bronze, ship carvings), short visit to A1 (Iron Age farm, bog iron) | A trader's apprentice, then a smith's | **Iron from the bog, and runes** (writing) |
| 8 | **The Viking Age** | ~AD 793 to ~1066 (unverified) | **A1 Naeroyfjord** (Gudvangen; a reconstructed Viking village, Njardarheimr, stands there today, checked) | A young farmer and boatbuilder | **The sea road and the written law** |
| 9 | **The empty valley** (medieval) | ~1370 (after the Black Death reached Bergen by ship in 1349, checked; Hanseatic office at Bryggen from ~1360, checked) | **A1 Naeroyfjord**, deserted farms; trade to Bergen | A family resettling an empty farm | **Stockfish trade and the market** (money economy) |
| 10 | **The fjord farm village** (1800s) | ~1850s (my call) | **A1 Naeroyfjord, Skarvik village** (owner 23:24: the built valley + village is this chapter) | A young villager | **Steam and the outside world** (steamers, letters from America, matches) |
| 11 | **Power and roads** (industrial/modern) | ~1890 to ~1960 (Tyssedal hydropower from 1906, checked; other dates unverified) | **A1 Naeroyfjord** (road, tourism, small power plant); optional visit to Odda/Tyssedal | A road builder's child, later a tourist guide | **Electricity** |
| 12 | **Today** | 2020s (Naeroyfjord a UNESCO World Heritage site since 2005, checked) | **All anchors** (A1, A2, A3, A4) on the Long Map | A descendant: hiker, kayaker, field-school student | No next era. The ending: find every trace your line left. |

Why these twelve (my call): each era adds exactly one idea the player can feel in their hands (walk, cut, keep fire, speak, sew, sail, farm, smelt, trade by sea, buy and build, use power, look back). Owner's list is covered: first ground walkers, Homo erectus and fire, sapiens out of Africa, Ice Age hunters, first settlers after the ice, farming, Bronze/Iron, Viking, medieval, 1800s, industrial/modern, today.

### 2.3 Era cards
Scope cost: **S** = mostly reuse; **M** = new props and characters on an existing terrain; **L** = new terrain + new kit; **XL** = new terrain, new body type, new fauna, new audio type.

**Era 1. From the trees to the ground** (A2, scope XL)
| Aspect | Design |
|---|---|
| Look | Lake-margin woodland and grass mosaic, fig and acacia-like trees, volcanic ridges, soda flats with flamingo-pink water at the edge (semi-historic: plants and animals are modern-looking cousins of the real ones, my call) |
| Actions | Climb trees (v1 climb system, trees are the safe home), walk upright in short bursts that grow longer, carry food in the arms (8 kg), forage fruit, nuts, termites, tubers, groom, alarm call, build a night nest in a tree, crack nuts with a hammerstone |
| Core loop | Wake in the trees -> come down to forage -> watch for danger -> carry food back -> share and groom -> climb up before dark |
| Two acts | Act 1 (~6-4 Mya): learning the ground; upright walking distance grows by use (40 m -> 400 m). Act 2 (~3.3 Mya): the band uses stones; the player finds a stone that cuts |
| Unlock | Key discovery: strike a flake and use it to open a carcass or tuber; plus 3 of 4 milestones (reach the far waterhole on foot, raise the keepsake stone, lead the band to a fig tree, sleep 3 nights in the band's best tree) |
| Fire | Fire is a danger: a wildfire event on the dry plain. The band forages roasted seeds and insects on the burnt ground after it passes (behaviour seen in chimpanzees today, unverified). No control |
| Animals | Elephants, antelope, giraffe, hippo, crocodile, big cats, hyenas (have model), baboons, vultures, flamingos |
| Speech, trade | No language. 12 call types (alarm, contact, food, come, play, distress...) and gestures (point, beckon, reach, offer). No trade: food sharing and grooming build trust |
| Survives | The keepsake stone (section 4.2), the Rift map layer, the band's trust shown in Era 2 |

**Era 2. Keepers of the fire** (A2 again, a drier age; scope L, reuses Era 1 terrain and most plants)
| Aspect | Design |
|---|---|
| Look | Same Rift terrain, drier: more open grassland, shrunken lake, ash on burnt hills, a rock shelter set piece |
| Actions | Long-distance walking and running, carry embers, gather fuel, feed and shelter a fire, cook, make a handaxe (Acheulean, ~1.7 Mya, unverified), scavenge with the group (approach in a group, never fight), gather, sleep on the ground by the fire |
| Core loop | Keep the fire -> fetch fuel and food in rings around it -> cook and share -> keep it alive through the night -> move camp with an ember when the water fails |
| Unlock | Key discovery: carry an ember from a wildfire to camp and keep that fire alive 3 nights in a row; plus 3 of 4 (cook a tuber, keep predators out of camp all night, make a handaxe, lead the band to a new water source) |
| Fire | Stages 1-3 of section 6: find natural fire, carry embers, keep it alive. Fire lets the band sleep on the ground instead of in trees (a hypothesis in human evolution research, unverified): this closes the "from the trees to the ground" arc |
| Animals | As Era 1 plus herds that follow rain; predators circle a camp without fire |
| Speech, trade | Calls, gestures, pointing, imitation; no words (my call: the evidence is unknown). Sharing only |
| Survives | Fire skill (Era 3 starts able to keep fire), the handaxe shape, the Rift map with the player's camps |

**Era 3. Words by the sea** (A3; act 2 in a desert canyon; scope L, act 2 reuses the Wadi Rum draft terrain)
| Aspect | Design |
|---|---|
| Look | Cave above a rocky shore, dune fields, fynbos-like shrubland, kelp, big swell. Act 2: red desert canyon and the narrow sea crossing to the north |
| Actions | Gather shellfish at low tide (tide timetable from the sim), grind ochre, drill shell beads, heat-treat stone in the fire, make fire with a hand drill, name places (the player assigns one of 3 pre-voiced names to a place; it sticks), tell a story at the fire (pick 1 of 3 story cards = which lore spreads) |
| Core loop | Read the tide -> gather -> make (beads, ochre, tools) -> give gifts to a neighbour band -> hear their news -> follow a story to a new place |
| Unlock | Key discovery: language and signs (first band-to-band gift exchange). Then act 2: lead the family along the coast and across the dry north (~70-50k years ago, unverified) |
| Fire | Stage 4 begins: hand-drill friction fire. Fire as tool: heat-treating stone |
| Animals and sea | Seals, whales and dolphins offshore, penguins on the rocks, sharks, eland, ostrich |
| Speech, trade | Language exists. Voice: an invented tongue with English subtitles, or English as a film convention (ask; my pick: invented tongue in Eras 3-4, English from Era 5). Trade: gift exchange of beads and ochre; v1 reputation tracks start here (band trust) |
| Survives | Language (all later eras talk), the bead string on the keepsake, the first lore entries |

**Era 4. Painted caves** (A4; scope L)
| Aspect | Design |
|---|---|
| Look | Limestone valley with cliff shelters, cold steppe and pine-birch woods, a river with salmon runs, a deep painted cave lit only by fat lamps |
| Actions | Track herds (reindeer, horse, bison), support the group hunt (drive, signal; kill off screen), fish salmon, sew clothing with an eyed needle, make fat lamps, make fire with flint and pyrite, paint in the cave at authored sockets, befriend a wolf that becomes the band's dog |
| Core loop | Read the season -> follow the herds -> process (hides, sinew, fat) -> sew and paint -> winter camp by the fire |
| Unlock | Key discovery: sewn fur clothing (clothing value 0.5, section 6.5) + the dog; then follow the reindeer north as the ice melts |
| Fire | Fire makes the cold survivable: a freezing, wet, windy night without fire is a setback before dawn (8.1 h to Warmth 0, my calc); with a windbreak and a camp fire it is +8.3/h (my calc) |
| Animals | Reindeer, horse, steppe bison (have a bison model), aurochs, mammoth, woolly rhino, cave lion, cave bear (bear model as stand-in), wolf (have model), ibex, salmon |
| Speech, trade | Language; long-distance gifts (sea shells far from the sea, unverified for this valley) |
| Survives | The dog's line (a dog follows the player in Eras 5-12, different breeds), the painting the player made (seen again in Era 12), sewn clothing |

**Era 5. After the ice** (A1 Naeroyfjord; scope M: same DEM, new vegetation state, new camp kit)
| Aspect | Design |
|---|---|
| Look | Same fjord, ~11,000 years younger: sea higher up the valley floor (the shoreline value must come from post-glacial sea-level data, unverified), fresh scree and moraine, a glacier tongue still in the upper valley, pioneer birch and pine only (no spruce), bare rock, meltwater, no buildings |
| Actions | Paddle a skin boat (row model), fish, gather shellfish and birds' eggs, set traps, watch seals and porpoises, build a tent/hut, make fire with flint and pyrite, raise a cairn, scratch a rock carving at an authored socket, place the family hearth at one of 6 hearth sockets (a trace, section 3) |
| Core loop | Paddle in -> find a camp place -> fire, shelter, food -> explore one more bend of the fjord -> return before weather turns |
| Unlock | Key discovery: the coast road (open the boat route to the outer coast and back with trade goods); plus 3 of 4 (hearth placed, cairn raised, winter stores for 30 days, first sighting of the "long fish") |
| Fire | Flint and pyrite; tinder fungus carried in a pouch (the Iceman, ~3300 BC, carried tinder fungus, unverified); keeping fire in a wet climate needs shelter (rain loss, section 6.3) |
| Animals and sea | Reindeer on the heights, red deer, elk/moose (have models), bear, wolf, fox, hare, eagle, gulls; seals, porpoises, orcas (rare), herring shoals, salmon, basking sharks (rare) |
| Speech, trade | English voice from here (ask). Barter with the outer-coast band (flint, seal oil, furs); v1 price formula in barter units |
| Survives | The hearth stone, the cairn, the carving, the "long fish" story -> all appear in Eras 8-12 |

**Era 6. First fields** (A5 Jaeren, optional anchor; scope L. If A5 is cut, this era moves to A1 at a smaller scale, ask)
Look: flat, windy moraine coast, boulder fields, heath, long sand beaches. Actions: clear a field with controlled burning, sow and harvest grain, herd sheep and cattle, make pottery in an open fire then a pit kiln, polish a stone axe, build a longhouse. Loop: season plan -> work the field -> store -> feast -> trade. Key discovery: farming + pottery. Animals: sheep, cattle, red deer, seals, seabirds. Speech: English; barter. Survives: the clay pot (keepsake cord gets a clay bead), grain (all later eras farm).

**Era 7. Bronze and iron** (A5 + short A1 visit; scope L)
Look: farms with longhouses, bronze glinting in a chieftain's hall, ship carvings on smooth rock by the sea. Actions: trade goods for bronze that comes from far south, cast in clay moulds (charcoal fire, bellows), carve a ship image at an authored rock socket (a trace), then at A1: dig bog ore, burn charcoal, smelt iron in a small furnace, learn runes. Key discovery: iron from the bog + runes. Fire: stage 6, smelting (fire temperature as a managed meter, section 6.6). Survives: runes (the player's name rune on later traces), the ship carving.

**Era 8. The Viking Age** (A1; scope M: same DEM, Viking farm kit, longship)
Look: the fjord as today's coastline (roughly; unverified), farms on the shore benches, longhouses with turf roofs, boathouses, a longship. Actions: farm, build a boat (v1 building stages), sail the fjord and out to the coast, attend the Thing (assembly, choose 1 of 3 pre-voiced cases to speak for), carve a rune stone, trade with hacksilver (weighed silver; price formula with weight), raise a burial mound for an elder (a trace; the burial itself is a quiet ceremony). Key discovery: the sea road + written law. Fire: the long hearth in the hall, flint and steel, a beacon cairn on the peak (my call). Animals: as Era 5 minus reindeer at sea level, plus sheep, goats, horses, cattle. Legends: lindorm, hafgufa (section 7). Survives: the burial mound, the rune stone, the boathouse site.

**Era 9. The empty valley** (A1; scope S-M: Era 8 and Era 10 kits recombined, a stave church)
Look: grown-over fields, some farms empty after the plague years, a small stave church. Actions: resettle and repair an empty farm, ferry stockfish and furs toward Bergen (abstract T3 market, v1 5.5), pay a tithe, walk the church path. Key discovery: market trade with money. Survives: the church site, the farm names, coins.

**Era 10. The fjord farm village, 1850s** (A1 Skarvik; scope S: this is the built valley; it is Slice 01, section 13-14)
Look: what exists: Naeroyfjord DEM, turf-roof timber houses, boathouses, pier, skigard fences, fish racks, pine/spruce/birch forest, waterfall. Actions: everything in v1 slice 01 (walk, run, climb, swim, gather, craft, build, buy, sell, talk, sleep) plus the fire system (flint and steel, hearth, smokehouse, smithy). Loop: v1 section 2 unchanged. Key discovery: steam and the outside world (the first steamer call, a letter from America, matches at the trader's stall). Speech: English, fully voiced (v1 section 9). Survives: the village itself (seen in Eras 11-12), the player's house, the family book.

**Era 11. Power and roads** (A1; scope M: road, power house, pylons, steamer, early cars, tourist hotel)
Actions: build a road switchback above the valley (v1 building stages at road scale), guide tourists to viewpoints (paid by tips: a new trade loop), help build a small power plant at the falls, string the power line to the village, send letters. Key discovery: electricity (the village lights come on, the hearth becomes a stove). Legends: Selma of Lake Seljord, told by a visitor (first written account 1750, checked). Survives: the road, the power house, the photo album.

**Era 12. Today** (all anchors; scope M per anchor: modern overlay props, people in modern clothes, signs, a ferry, a field-school dig)
Actions: hike, kayak, ride the ferry, take photos (journal pages), join a field-school dig that uncovers the player's own Era 5 hearth, visit a cave replica, see the keepsake stone in a museum case. Fire: a lighter; you may only light a fire where it is allowed (Norwegian fire ban near forests in summer, dates unverified). The final scene: you light a small fire at the hearth socket where your Era 5 pioneer lit hers. Key discovery: none. The game's end condition: the trace collection (section 3.4).

---

## 3. Anchor places and traces (owner 23:24)

### 3.1 The anchors
Each anchor is one real terrain from open elevation data, built once, then re-dressed per era by a data layer (`EraLayerDef`): water level, ice, vegetation mix, buildings, roads, props, people, animals, light and weather tables. The heightfield never changes; only what sits on it (and the sea level) does.

| # | Anchor | Real place (data) | Eras visiting | What time changes |
|---|---|---|---|---|
| **A1** | **Naeroyfjord / Skarvik** | Kartverket DTM 10 + 2 m near area + chart soundings (built) | 5, 7 (short), 8, 9, 10, 11, 12 | Ice retreats; shoreline drops; forest closes in; spruce arrives (date unverified); farms rise, empty, return; road, power line, ferry |
| **A2** | **Rift lake** (West Turkana, Kenya) | Copernicus GLO-30 (licence verified 10-10 for other tiles; this tile needs the same credit) | 1, 2, 12 | Lake rises and shrinks; woodland gives way to grassland; volcanic ash layers; today a dry fossil field with a research camp |
| **A3** | **Southern Cape coast cave** (Blombos-like) | Copernicus GLO-30 + authored cave | 3, 12 | Sea level: in glacial times the shore lay much farther out (amount unverified); today the cave sits above the surf |
| **A4** | **Vezere cave valley** (Dordogne) | Copernicus GLO-30 (France has finer open DEMs too, licence unchecked) + authored cave | 4, 12 | Steppe to oak forest; today a village, a museum and a replica cave |
| **A5** (optional) | **Jaeren coast** (Rogaland) | Kartverket DTM | 6, 7 | Forest to heath and fields; longhouses; ship carvings |

Why A1 carries most eras (owner 23:24): it is built, measured on the phone, and the fjord's own history (first settlers, Viking farms, plague-emptied farms, the 1800s village, roads, tourism, UNESCO) has a real event for almost every later era. Seven of twelve eras use it, so one terrain pays for more than half the game.

v1 regions: R1 Skarvik becomes A1. R2 Kefalonia and R3 Wadi Rum draft terrains are kept as candidate places (Wadi Rum = Era 3 act 2, the walk north; Kefalonia = optional Bronze Age trade voyage in Era 7, ask). R4 Delta and R5 Highlands are dropped.

### 3.2 Traces: what carries from one era to a later one
A **trace** is a thing the player made, placed, named or witnessed in one era that shows up, changed by time, in later eras at the same anchor.

```
TraceDef {
  id, anchor_id, socket_ids[]          // authored places where it can exist
  created_in_era, cause                // player_action (build_hearth, carve, raise_cairn, name_place,
                                       //   bury_keepsake_bead, paint) | witnessed (legend_sighting, wildfire, whale_stranding)
  forms { era_id: { mesh/state, discoverable_by: [look, dig, rumor, museum], journal_page } }
  seeds_lore [ { era_id, rumor_id, truth_state } ]   // the legend this trace becomes later
}
TraceInstance { trace_id, socket_id, created_day, player_choice (which of 3 names, which story) }
```

Rules (my call):
- Traces go into **authored sockets** only (e.g. 6 hearth sockets, 4 cairn sockets, 5 carving rocks per anchor). The player chooses which socket; content stays bounded and every later form is pre-built for every socket.
- A trace only exists in later eras if the player made it. If they skipped it, the socket shows the default history (someone else's hearth), so no era breaks.
- Finding your own trace in a later era: **Echo** (journal page, Wayfinder +5, a short pre-voiced line from the player character, e.g. "I know this stone.").

### 3.3 A1 trace chain (worked example)
| Era 5 (you do/see) | Era 8 | Era 9 | Era 10 (slice) | Era 11 | Era 12 |
|---|---|---|---|---|---|
| Place the family hearth at socket H3 by the river mouth | A ring of fire-cracked stones under the turf; locals call it "the giant's hearth" (lore, exaggerated) | Under a field; the plough turns up charcoal | A farmer's tale: "The old ones say a giant cooked whales by the river" (exaggerated) | Road workers find black earth, report it to a museum (outdated rumor: "nothing there now") | Field-school dig at H3 dates the hearth to ~9000 BC; you help uncover it (true) |
| Raise a cairn on the shoulder above the falls | Becomes a way-marker on the summer-farm path | Overgrown | A beacon cairn (varde) on the same spot | A trig point beside it | On the hiking map |
| Witness the "long fish" (two basking sharks nose to tail) | "A sea serpent lives in the fjord" (exaggerated) | Told as a warning to boatmen | Sea serpent rumor + legend sighting chance (section 7) | A newspaper story (false: a hoax photo) | A museum text explains basking sharks (true) |
| Hear the waterfall gully "sing" in a west wind | "The mountain sings" (partly true) | "The fossegrim plays behind the falls" (folk belief) | The Singing Cavern wonder behind Bluewater Falls (v1, slice) | The pipe intake changes the sound: "the fossegrim left" (invented) | Sound walk sign at the viewpoint |

### 3.4 Traces and the rumor system
A rumor in one era can be history the player saw in another. Each lore entry may name a `source_trace`. When the player hears a rumor whose source they made or witnessed:
- The journal links the rumor to the original event ("You were there: Era 5, day 12").
- The player can **tell what really happened** (one pre-voiced choice per rumor, 2 versions: the true account, or let the legend live). Telling the truth flips that rumor's instances to True among NPCs who hear it from the player (v1 rumor hop rules, confidence 0.9). Letting it live keeps the legend and gives a small Community reputation bonus (+2) with the storytellers (my call).
- **Trace collection** is the long-term goal: 40 traces in the full game (A1: 18, A2: 8, A3: 6, A4: 8; my call). The ending in Era 12 shows the line's map with every Echo found.

---

## 4. Cross-era progression: what survives

| Carries over | How | Shown as |
|---|---|---|
| **Knowledge** | Each era's key discovery becomes a permanent skill baseline: fire keeping (2), language (3), sewing (4), boats (5), farming (6), metal and runes (7)... Actions learned earlier start at a higher skill in later eras | Journal "Hearth Book": one page per discovery, illustrated |
| **The family line** | The player is always "of the line". At era end the current character hands the keepsake to a younger one (section 4.3) | Family tree on the Long Map; one portrait per era |
| **The keepsake stone** | One object through all eras (section 4.2) | Always in the bag; changes look per era |
| **The map** | The Long Map: anchors x eras grid; each cell is a playable save state once finished | Map screen with an era slider per anchor |
| **Traces** | Section 3 | Echoes in the journal |
| **The dog's line** | From Era 4: a dog companion in every later era (different breed per era) | Follows, finds tracks, barks at legends |
| **Reputation** | Does not carry (new people each era). Explorer (Wayfinder) reputation is the one global track that carries (v1 5.7) | Wayfinder band on the profile |

### 4.1 Era progression rule
Each era has 1 key discovery + 4 milestones. The next era unlocks when the key discovery is done and 3 of the 4 milestones are done (my call). The player chooses when to move on at a fire ("Pass the stone" action at the home hearth). Nothing forces the move; the era keeps simulating until then.

### 4.2 The keepsake stone
Based on a real object: the Makapansgat pebble, a jasper cobble with natural face-like marks, about 3 million years old, found far (~32 km) from its source, so possibly carried by a hominin (checked; the "carried as a face" reading is a hypothesis). In game it is the line's stone, not the real object (semi-historic licence, my call).

| Era | Keepsake change |
|---|---|
| 1 | Found in a stream; the player carries it back to the band's tree (milestone) |
| 3 | Bound in a cord with a shell bead |
| 4 | Ochre rubbed into the face marks |
| 5-7 | Clay bead (6), bronze wire wrap (7) |
| 8 | A rune scratched on the back: the line's name |
| 10 | Sits on the grandmother's shelf by the hearth (slice) |
| 12 | In a museum case labelled "family heirloom, origin unknown" until the player adds the journal; the label changes |

### 4.3 Handing over (era transition)
A 40-60 s scene at the home hearth: the current character, now older, gives the keepsake to a child of the line; the camera rises over the anchor while time-lapse runs (ice melting, forest growing, houses rising and falling); the new era's title card. No death is shown or named. Skippable after the first viewing.

### 4.4 The Long Map
After Era 12, or for any finished era earlier, the player can open any anchor in any finished era from the map. Revisited eras keep their sim running (v1 T3 abstract tick when away). An era slider on an anchor plays the time-lapse of that place across the eras the player has finished.

---

## 5. Core loop by era type

| Era type | Eras | Loop | v1 economy used? |
|---|---|---|---|
| **Band, no words** | 1-2 | Forage -> watch -> carry -> share -> groom -> nest (1) or fire (2) | No prices. Food sharing and grooming fill trust (v1 affinity) |
| **Band with words** | 3-5 | Read season and tide -> gather/track -> make -> gift or barter -> hear news -> go further | Barter: v1 price formula in "value units" per camp |
| **Settled** | 6-9 | Plan the season -> work fields/craft -> store -> trade -> build -> feast | v1 formula; weighed silver in 8; coins from 9 |
| **Village and market** | 10-12 | v1 section 2 unchanged: explore -> gather -> process -> trade -> build -> connect -> unlock | Full v1 economy (5.3) |

Time scale stays v1: 1 in-game day = 24 real minutes; night 20:00-06:00 = 10 real minutes.

---

## 6. Fire (owner: build and light a fire, keep it alive, stay warm)

Fire is the one system that runs through every era. It grows from a danger (Era 1) to a kept treasure (2) to a tool you make (3-5) to industry (6-11) to a choice (12).

### 6.1 Fire stages by era
| Stage | Era | What the player can do | Input |
|---|---|---|---|
| 1. Witness | 1 | See wildfire, flee, forage on burnt ground after | - |
| 2. Find and carry | 2 | Take an ember from a lightning or wildfire, carry it in a carrier | Action at a burning branch |
| 3. Keep alive | 2+ | Feed fuel, shelter from rain and wind, bank to embers for the night | Action at the fire (feed / bank / revive) |
| 4. Make by friction | 3+ | Hand drill (3), bow drill (5+) | Hold Action (6.4) |
| 5. Make by sparks | 4+ | Flint and pyrite (4-7), flint and steel (7-10), matches (10 rare, 11 common), lighter (12) | Tap Action (6.4) |
| 6. Fire as tool | 3+ | Heat-treat stone (3), lamps (4), clear land (6), pottery kiln (6), casting and smelting (7), charcoal (7+), smoking fish (5+), smithy (8+), beacon (8+), stove (11) | Station use |

### 6.2 Fire state (data)
```
FireDef   { id, size: small | camp | big | hearth | kiln | forge, radius_m, burn_kg_h, max_heat }
FuelDef   { id, duration_mult, ignite_ease 0-1, smoke 0-1, wet_penalty }
FireState { heat 0-100, fuel_kg, fuel_mix[], sheltered: bool, windbreak: bool, banked: bool, age_h }
```
Sizes (my call): small 1.5 kg/h, radius 2.5 m; camp 3 kg/h, 5 m; big 6 kg/h, 8 m (signal, predators). Hearth = camp, always sheltered. Fuel duration multiplier vs branch wood: dry grass/dung 0.4, twigs 0.6, branch wood 1.0, split logs 1.3, peat 1.2, charcoal 2.0.

Fuel for one 10 h night, camp fire (my calc): branch wood 30 kg calm, 39 kg in wind 0.6 open, 34.5 kg with a windbreak; split logs 23 kg calm; twigs 50 kg. The Era 1-2 arm carry is 8 kg, so one night of fire = 4-5 trips or the band's help: keeping fire is a social job (my call, intended).

### 6.3 Keeping it alive
| Factor | Rule (my call) |
|---|---|
| Burn | `burn_kg_h = size_rate * (1 + 0.5 * wind_eff) / fuel_duration`; `wind_eff = wind * (0.5 if windbreak else 1)` |
| Heat | Heat moves 20/h toward `min(100, 25 + fuel_kg * 6)`; at fuel 0 heat falls 30/h |
| Rain (unsheltered) | Light rain -15 heat/h, heavy -40/h; sheltered or hearth: 0 |
| Embers | Heat below 10 = embers. Embers last 2 h with no fuel, then out. Feed at ember stage = revive (Heat +15 instantly if fuel is dry) |
| Banking | "Bank" covers the fire with ash: burn x0.25, heat capped 25, embers last 8 h. Used for nights (hearth) and in Eras 2-5 to keep fire while away |
| Wet fuel | Wet fuel (rained on, unstored) burns x0.6 duration and smokes; can't light from embers below heat 30 |
| Ember carriers | Smouldering branch 1 h; tinder fungus or dung wrap 4 h; horn or clay ember pot 12 h. Halved in rain unless covered (my calc: 4 real minutes for the fungus wrap, 2 in rain) |
| Spread | Fires never spread to buildings or forest by accident (my call, youth audience). Only authored events burn land: wildfire (1-2), controlled field burning (6) |

### 6.4 Making fire (touch input, no precision gestures)
| Method | Input | Success rule (my call) |
|---|---|---|
| Hand drill (3+) | Hold Action. A glow ring fills | Fill rate 12/s x tinder dryness (0.3 wet - 1.0 dry) x (0.7 + 0.3 x skill/100). Wind above 0.6 without a windbreak drains 8/s. Full ring = ember; then tap Action 3 times within 3 s to blow it to flame |
| Bow drill (5+) | Hold Action | As hand drill, fill 20/s |
| Flint + pyrite (4-7) | Tap Action, one spark per tap (max 2 taps/s) | Catch chance per spark 25% x tinder quality (tinder fungus 0.9, birch bark 0.7, dry grass 0.5) |
| Flint + steel (7-10) | Tap Action | 45% x tinder quality |
| Matches (10 rare import, 11) | Tap once | 95%; wind above 0.6 blows it out 20% of the time |
| Lighter (12) | Tap once | 100%; fire allowed only at legal spots |
Feedback: spark particles 0.15 s, a soft strike click, tinder smoke curl, warm vignette pulse 0.4 s when the flame takes, light haptic tick per spark, one longer haptic (60 ms) on success.

### 6.5 Fire, Warmth, Hunger, Rest (v1 section 4 tied in)
Warmth per in-game hour (my call; v1 named the meter but set no rates):
```
loss  = band_temp (mild 0, cool -4, cold -8, freezing -14) + night -3
        + (if not sheltered) wet -6 + wind * -3
loss *= 1 - clothing (none 0, hide wrap 0.3, sewn furs 0.5, wool + oilskin 0.6)
loss *= preset drain (Gentle 0.5, Wayfarer 1.0, Hardy 1.5)
gain  = 30 * (1 - distance / fire_radius) * heat / 100      (0 beyond the radius)
```
Worked cases, sitting 1.5 m from the fire (my calc, `tools/fire_calc.py`, Wayfarer preset):
| Case | Warmth per h | Time from 100 to 0 |
|---|---|---|
| Era 1-2, cool night, no fire, no clothes | -7.9 | 12.7 h (a 10 h night is survivable; predators are the pressure) |
| Era 2, cool night, camp fire heat 80 | +8.9 | never |
| Era 4, freezing, wet, windy, sewn furs, no fire | -12.4 | 8.1 h (setback before dawn) |
| Era 4, same with windbreak + camp fire 80 | +8.3 | never |
| Era 10, cold rain night outdoors, wool + oilskin | -7.5 | 13.3 h (Hardy x1.5: 8.9 h, setback) |
| Era 10, in house, hearth heat 60 | +8.2 | never |
| Era 10, outdoors, small fire 80, rain | +2.1 | never (barely) |

Other ties:
- **Hunger**: cooked food gives Fullness x1.5 vs raw and +10 Warmth at once. Some foods only count cooked (tubers in Era 2+, most meat). Fullness drain stays v1 (-4/h awake).
- **Rest**: sleeping by a fire that burns all night = bedroll (75% Rest, v1). If it goes out, Rest gain stops when heat hits 0 and (Eras 1-5) predators come to the camp edge: the band wakes and climbs/huddles (setback-lite: the night ends, Rest stays where it was).
- **Light**: a fire lights radius x2 at night; caves need a lamp or torch (Era 4+). Torches burn 0.5 h (my call).
- **Predators** (Eras 1-5): a fire with heat >= 40 keeps predators beyond 25 m. Without fire, nights on the ground carry a 30% chance per night of a predator visit (Wayfarer; Gentle 0%, Hardy 50%; my call) that ends the night early. They never touch the player or the band.
- **Smoke signals** (Era 3+): a big fire with green fuel makes a column visible 8 km; NPC bands and later villages answer (beacon cairn in Eras 8-10). Used to call boats, guide lost NPCs, and in the slice to signal the trader boat.

### 6.6 Fire as industry (Eras 6-11)
Kilns and forges use a **heat target band**: keep heat inside a band for a duration by feeding fuel and working bellows (hold Action = bellows, +12 heat/s, decays 6/s, my call). Pottery: 60-75 for 1 h. Bronze casting: 80-95 for 20 min. Iron bloom: 85-100 for 2 h with charcoal only. Smithing: 70-90 per work step. Missing the band wastes fuel and time, never the material (no fail state, my call).

---

## 7. Legends: dragons, sea creatures and local lore

### 7.1 Design rule
Semi-historic means: **legends live in the lore and rumor layer**; the world itself is real. The player meets three tiers (my call):

| Tier | What | Frequency | How the player meets it |
|---|---|---|---|
| Real sea and land life | Whales, orcas, seals, porpoises, basking sharks, herring shoals, salmon runs; mammoths and cave lions in their era | Common to uncommon, sim-driven (season, prey) | Seen, followed, recorded in the journal. Never killed for progress |
| Real things that look like legends | Two basking sharks nose to tail (a "serpent"), an oarfish at the surface, a whale back like an island, a giant squid carcass on a beach, fossil bones in a cliff ("dragon bones"), a lightning-lit storm shape | Rare wonder events | A **wonder** (v1 5.9) whose journal page says what it was |
| **Legend sightings** | A dragon silhouette over a ridge in a storm, a sea serpent rising at dusk, a lindorm sliding into scree | Very rare: 2% per eligible evening, at most once per type per era; eligible = the matching rumor is held + Wayfinder >= Trusted + the right weather and place (my call) | Fully rendered for 4-8 s at 300-800 m, half hidden by mist or spray. No photo, only a journal sketch. Never confirmed. Afterwards the player's own sighting spreads as a new rumor (exaggerated state) |

Dragons and sea creatures are encountered, followed, witnessed and recorded; never fought, hunted or captured. Whether a real dragon should ever be confirmed is open (ask; my default: never confirmed).

### 7.2 Signs (Eras 1-2, no language)
Before words, the rumor system (v1 5.6) runs as **signs** read from the world, with the same five truth states. `RumorDef` gains `delivery: sign` and a visual/sound cue instead of a voiced line.

| Era | Sign | Truth states it can take |
|---|---|---|
| 1 | Vultures circling to the east | True (a carcass), outdated (already eaten) |
| 1 | Baboon alarm barks at the waterhole | True (a big cat), false (a falling branch) |
| 1 | The old female points toward the fig grove | Partly true (figs not ripe yet) |
| 1 | Smoke on the horizon | True (wildfire coming) |
| 2 | A lightning-struck tree still smouldering on the ridge | True (an ember source), outdated after rain |
| 2 | Hyena whoops after dark | Exaggerated (one hyena, not a clan) |
| 2 | Fresh tracks of a herd heading south | True; partly true (old tracks after the rain) |
| 2 | Flamingos lifting off the far lake | True (fresh water inflow, my call) |

### 7.3 Lore per era (3-5 entries each)
Lore for Eras 3-7 is (invented) in-world storytelling: no records of those peoples' stories exist. Real traditions appear from Era 8 on and must be checked against sources before game text ships. Lore about living cultures outside Norway is not used without a cultural review (my call).

| Era | Place | Lore entry | Truth state | Leads to / trace |
|---|---|---|---|---|
| 3 | A3 cave | "The big fish that breathes smoke" | True (a whale blow) | Whale wonder |
| 3 | A3 | "Fire sleeps inside the red stone" (invented) | True (heat-treated stone flakes better) | Fire-as-tool tutorial |
| 3 | A3 | "Once the sea walked away and you could walk to the islands" (invented) | True (lower glacial sea level) | Era 12 museum text |
| 3 | A3 | "Beyond the dunes the land never ends" | Exaggerated | Act 2, the walk north |
| 4 | A4 cave | "The beast with two straight horns lives in the deep cave" (painting in Lascaux called "the unicorn", unverified) | Partly true (a painting, not an animal) | The player paints at a socket; Era 12 replica cave shows it |
| 4 | A4 | "The great hairy ones have left the south valley" | Outdated (mammoths still in the north valley) | Mammoth wonder |
| 4 | A4 | "A cave lion sleeps in the third cave" | Exaggerated (it is a cave bear) | Legend-tier encounter, seen from a safe ledge |
| 4 | A4 | "Salmon come when the first frost whitens the grass" (invented) | Partly true | Salmon run event |
| 5 | A1 | "A giant of ice sleeps up the valley; he groans at night" (invented) | Partly true (the glacier, calving and cracking) | Glacier wonder; seed of later giant tales |
| 5 | A1 | "Fire-stones lie on the outer beach" | True (flint pebbles, unverified for this coast) | Coast road milestone |
| 5 | A1 | "A long fish as long as three boats swims in the fjord" | Exaggerated (two basking sharks) | **Trace**: becomes the sea serpent legend |
| 5 | A1 | "The mountain sings in the west wind" (invented) | Partly true | **Trace**: becomes the Singing Cavern |
| 6 | A5 | "The big stones walked here in the night" (invented) | False (glacial boulders) | Erratic boulder wonder |
| 6 | A5 | "Smoke in the forest means new fields" | True | Field burning |
| 6 | A5 | "The sea gives golden stone after storms" | Exaggerated (amber is rare here, unverified) | Beachcombing |
| 7 | A5 | "Bronze comes from the land where the sun lives" | Partly true (metal came from far south) | Trade voyage (Kefalonia, optional) |
| 7 | A1 | "Iron grows back in the bog if you wait" | Partly true (bog ore re-forms slowly, unverified) | Bog iron |
| 7 | A1 | "The giant's hearth by the river mouth" | Exaggerated (the player's Era 5 hearth) | **Trace** H3 |
| 7 | A5 | "The ship carvings carry the dead over the sea" | Unknown (scholars disagree, unverified) | Ship carving socket |
| 8 | A1 | "A lindorm lives in the scree under the north wall" (lindorm: Scandinavian dragon-serpent folklore, unverified) | False | Legend sighting: dragon shape in a storm |
| 8 | A1 | "Out at sea, hafgufa looks like an island and then sinks" (hafgufa in the Orvar-Odds saga, checked) | Partly true (a whale back, a giant squid) | Whale-back wonder |
| 8 | A1 | "The world serpent lies around the world in the sea" (Norse myth, Eddas, unverified dating) | Myth (no truth test) | Thing story card |
| 8 | A1 | "The first settler lies in the mound above the falls" | Exaggerated (the player's Era 5 cairn) | **Trace** cairn |
| 8 | A1 | "Whales strand on the west beach in autumn storms" | True | Whale stranding windfall |
| 9 | A1 | "The plague came by ship to Bergen" (1349, checked) | Outdated by 1370 (it has passed) | Empty farms |
| 9 | A1 | "The empty farm is haunted" | False | Resettle it |
| 9 | A1 | "A sea beast like an island" (King's Mirror, c. 1250, checked) | Partly true | Hafgufa wonder again |
| 9 | Bergen route | "Stockfish fetches double in Bergen this year" | True or outdated (market sim) | Trade run |
| 10 | A1 | "The fossegrim plays behind the falls at dawn" (waterfall spirit, fiddle-teacher in folk belief, unverified) | Partly true (the Singing Cavern) | Singing Cavern (v1) |
| 10 | A1 | "The huldra keeps the summer farm cattle" (Norwegian folklore, unverified details) | False | Summer-farm walk |
| 10 | A1 | "The nokk lures folk into the tarn" (Norwegian folklore, unverified details) | False (but the tarn is deep and cold: a real setback risk) | Tarn |
| 10 | A1 | "A sea serpent swims in the fjord" (Pontoppidan argued for sea serpents and the kraken, 1752-53, checked) | Exaggerated / legend sighting | **Trace** from Era 5 |
| 10 | A1 | "A giant cooked whales by the river mouth" | Exaggerated | **Trace** H3 |
| 11 | Visitor | "Selma, the serpent of Lake Seljord" (first written account 1750, checked) | Legend | Told by a Telemark tourist |
| 11 | A1 | "The power plant will light every house" | Exaggerated, later true | Power line |
| 11 | A1 | "The fossegrim left when they built the intake" (invented) | False | Singing Cavern sound changes |
| 11 | A1 | "There's nothing under the black earth by the river" | Outdated once dug | **Trace** H3 |
| 12 | A1 | "They found a hearth older than the pyramids" | True | Field-school dig at H3 |
| 12 | A1 | "Orcas follow the herring into the fjords in winter" | Partly true (common farther north) | Orca wonder |
| 12 | A1 | "A drone filmed a dragon over the fjord" | False (a hoax video) | Last legend sighting chance |
| 12 | Museum | "The face stone came from Africa" | True (the keepsake) | Ending |

### 7.4 Real sea life (A1 and A3)
| Animal | Where/when (my call unless marked) | Behaviour in game | Model status |
|---|---|---|---|
| Harbour seal, grey seal | A1 all eras, haul-out rocks | Hauls out at low tide, watches the player, slips into water within 15 m | New |
| Harbour porpoise | A1 | Small groups, short surfacings | New |
| Orca | A1 rare (1 in 20 days), A3 | Pod of 3-6 following herring; wonder | New |
| Minke / humpback whale | A1 rare, A3 seasonal | Blow, back, fluke; whale-back wonder | New |
| Basking shark | A1 summer, rare | Slow surface swimming, pairs = "serpent" | New (hammerhead model is the wrong species) |
| Herring shoal | A1 autumn-winter | Boid shoal under boats, gulls diving | New (cheap boids) |
| Salmon | A1, A4 rivers, autumn | Leaping at falls | New |
| Oarfish | A1 very rare | Surface sighting = serpent wonder (the species name glesne refers to a Norwegian place, unverified) | New |

---

## 8. Systems spec (v1 section 5, adapted)

All content is data, as in v1, plus new definitions: `EraDef`, `EraLayerDef`, `AnchorDef`, `TraceDef`, `KeepsakeStageDef`, `FireDef`, `FuelDef`, `IgnitionDef`, `CallDef` (wordless vocalisations), `LegendSightingDef` (a `WonderDef` type). No per-era code paths where data can do it (my call): an era is a data bundle that switches actions, recipes, speech mode and economy mode on.

| v1 section | Status in v2 |
|---|---|
| 5.1 Sim clock | Unchanged |
| 5.2 Chains A-D | Kept for Eras 10-12 (A1). Each era gets 2 chains of its own (examples below) |
| 5.3 Economy formula | Unchanged; unit = value units (barter, 3-7), weighed silver (8), coins (9-12). Era 10 coin: skilling (Norwegian coin of the time, unverified) |
| 5.4 NPC layers | Unchanged. In Eras 1-2, Layer 3 is **behaviour, not dialogue**: memories change who approaches, grooms, shares and follows |
| 5.4 Memory schema | Unchanged; new event types: `shared_food`, `groomed`, `kept_fire_for`, `carried_ember`, `taught_skill` |
| 5.5 NPC LOD | Unchanged |
| 5.6 Rumors | Unchanged; plus `delivery: sign` (7.2), `source_trace` (3.4), lore entries (7.3) |
| 5.7 Reputation | Band trust replaces Village in Eras 1-5; Merchant from Era 5 (barter); Wayfinder global and carries across eras |
| 5.8 Building | Unchanged stages; per-era building lists (nest platform 1, windbreak 2, hut 3-5, longhouse 6-8, timber house 9-10, road and power house 11) |
| 5.9 Wonders | ~3 per era + legend sightings (section 7); 36 wonders total (my call) |
| 5.10 Settlement growth | Band growth in Eras 1-5 (8 -> 14 -> 20 -> 30 people); v1 stages from Era 6 |

Example era chains (my call):
- **Era 2, dry season -> fire**: dry weeks -> waterhole shrinks -> herds and predators crowd it -> the band must camp near it -> fire becomes the only safe way to sleep there -> more fuel trips -> the player who keeps the fire gains trust from everyone.
- **Era 5, autumn storm -> stranding**: storm -> a whale strands on the west beach (5% per autumn storm) -> food windfall (oil, meat) -> the band stays longer -> winter stores reached -> one milestone done.
- **Era 10, cold snap -> firewood** = v1 Chain B, now driven by the fire system: each household hearth kept burning (unbanked) through a cold night uses 20-25 kg logs (my calc), so stock drains visibly.

---

## 9. Dialogue, calls and voice

| Eras | Speech | Audio source | Lines per NPC (my call) |
|---|---|---|---|
| 1-2 | No words. `CallDef`: 12 call types x 3 variants x 4 voice types (adult female, adult male, juvenile, elder) = 144 clips per era, shared by all band members | Designed from real primate and human non-verbal sound (recorded or licensed; not TTS). Source open (ask) | 0 lines; behaviour carries memory |
| 3-4 | Invented tongue + English subtitles (my pick, ask) | Pre-rendered TTS or recorded phoneme set | ~60 |
| 5-12 | English, fully voiced (v1 pipeline 6.1-6.2 unchanged) | Local TTS, licence-clean voice (still open from v1) | 148 (v1 slice budget) |

v1 section 6 (data flow, deterministic selection, Ingrid examples) stays in force for Eras 5-12. Lore and rumor lines are authored per truth state as in v1.

---

## 10. Controls (v1 section 7, adapted)

v1 layout unchanged (floating move stick left, camera drag right, Action 190 px, Traverse 170 px, Drop 140 px, Bag/Map/Journal top right, meters top left). Additions (my call):
- **Action at a fire** cycles by context: Feed (if fuel in bag), Bank (if night), Revive (if embers), Light (if unlit and an ignition item is carried), Cook (if raw food), Sit.
- **Hold Action** = drilling, bellows; **tap Action** = sparks, blowing on embers (section 6.4).
- **Call wheel** (Eras 1-2): the Talk icon opens 6 calls on a ring (Come, Food, Danger, Calm, Play, Look); tap one.
- **Point**: in all eras, hold on an NPC + drag toward a place = point there (used for signs, guiding, telling the truth of a trace).
- Era 1 locomotion: Traverse held on flat ground = knuckle-walk/run on all fours (fast), released = upright walk (slow, grows with use).

---

## 11. Movement and animation per era

v1 P0/P1/P2 lists stay for human eras (3-12). New sets:
| Set | Needed for | Animations |
|---|---|---|
| Hominin early (Era 1) | Player + band | Upright walk (short, wobbly at low skill), quadrupedal walk/run, tree climb (vertical, branch walk, hang, swing), nest build, sit, groom pair, carry in arms, forage (reach, dig, crack nut), alarm stand, sleep curled |
| Erectus (Era 2) | Player + band | Long stride walk and run, carry ember, crouch-feed fire, blow on embers, knap, sit by fire, sleep on ground |
| Fire (all) | Player + NPCs | Feed, bank, blow, drill (hand, bow), strike sparks, cook on stick/stone, warm hands, carry torch |
| Boat (5, 8, 10) | Player + NPCs | Paddle, row, sail trim (P2) |

Risk: realistic early-hominin bodies have no free rigged sources I know of (section 15, risk 1).

---

## 12. What v1 sections still apply

| v1 section | v2 home |
|---|---|
| 2 Core loop | Section 5 (village eras unchanged) |
| 3 Regions | Replaced by anchors (section 3) |
| 4 Survival | Section 6.5 (presets and setbacks unchanged; Warmth now has numbers) |
| 5 Systems | Section 8 |
| 6 Dialogue | Section 9 |
| 7-8 Controls, movement | Sections 10-11 |
| 9 Slice 01 | Section 14 (Era 10) |
| 9.4 Performance budget | Section 14.4 |
| 11 Names | Dropped; new names needed for a time-spanning game (ask) |

---

## 13. Production plan

### 13.1 First chapter: Era 10, the fjord farm village (Slice 01)
Owner decision 23:24: the built valley and village are the 1800s chapter. It is also my pick for the first chapter to ship:
1. **Reuse**: the Naeroyfjord DEM, 2 m near area, seabed, water, forest (90k trees), village kit (turf-roof houses, boathouses, pier, skigard, fish racks, boats), Ingrid and the scanned player, 10 animal species, the phone presets and PerfOverlay all exist for exactly this period.
2. **Every v1 system** (economy, NPC memory, rumors, building, growth, voiced dialogue) was specified for this valley and this period; it proves the systems the later eras inherit.
3. **The fire system** fits it fully: hearths, flint and steel, the smokehouse, the smithy, a beacon cairn, a cold autumn, and matches arriving as a costly import.
4. **Anchor mechanics** can be stubbed in it: trace sockets at A1 (hearth H3 etc.) shown in their Era 10 form with the default history; the keepsake on the grandmother's shelf; the Era 10 lore entries that point back to Era 5.

What it does not prove: the no-language eras, the hominin body, the era transition. Those are Chapter 3 and Chapter 2.

### 13.2 Roadmap (favouring the fjord terrain, owner 23:24)
| Chapter | Era(s) | Why next | Terrain reuse |
|---|---|---|---|
| 1 (Slice 01) | 10 | Built; proves all v1 systems + fire on the phone | A1 as built |
| 2 | 5 After the ice | Same DEM; proves the anchor idea (same place, two eras), traces (Era 5 hearth -> Era 10 tale), the handing-over transition, making fire anywhere, barter. Cheapest new era | A1: new EraLayer (sea level, ice, pioneer vegetation) |
| 3 | 1-2 From the trees, Keepers of the fire | The owner's opening and the origin of fire; biggest art risk, so start hominin art R&D during Chapter 1 | New A2 terrain (Copernicus pipeline exists) |
| 4 | 8 Viking Age | Third era on A1; longship and hall; strong lore (lindorm, hafgufa) | A1 |
| 5 | 12 Today (A1 only first) | Closes the A1 loop: the dig at H3, the ferry, the museum; makes the anchor promise pay off | A1 + modern overlay |
| 6 | 9 and 11 | Both mostly recombine Era 8, 10 and 12 kits on A1 | A1 |
| 7 | 3 and 4 | New anchors A3, A4 (caves, coast, Ice Age fauna) | New terrains |
| 8 | 6-7 | A5 Jaeren or folded into A1 (ask) | New or A1 |
| 9 | 12 at A2, A3, A4 | Today at every anchor; full ending | Overlays |

### 13.3 Asset list delta per chapter
| Chapter | New art needed (beyond what exists) | Size |
|---|---|---|
| 1 Era 10 | 1850s clothing for ~8 archetypes (current Ingrid wears modern denim bibs), 20 NPC variants, interiors of 2 houses with hearths, smokehouse, smithy + forge, stall, footbridge build stages, fire FX set (flame flipbook, embers, smoke, sparks, ember glow decal), night light preset + lantern, flint and steel, tinder, firewood/log piles, sea life (seal, porpoise, herring shoal, basking shark, minke whale, orca), sheep, goats, cows, horse, Singing Cavern interior, beacon cairn, legend sighting asset (serpent), keepsake stone | M |
| 2 Era 5 | EraLayer for A1 (sea level shift, glacier tongue mesh, moraine and scree dressing, pioneer birch/pine only), skin boat, tent/hut, fishing gear, Mesolithic clothing (furs, hide), 6-8 people, reindeer (none found yet), seal haul-out, cairn, rock carving decals, flint/pyrite, era-transition time-lapse | M |
| 3 Eras 1-2 | A2 terrain (DEM + lake, savanna/woodland vegetation set, acacia/fig trees, grass), hominin player + band bodies (2 species, 4 body types, fur/skin shaders), full hominin animation sets, African fauna (elephant, antelope, giraffe, hippo, crocodile (alligator model is the wrong species), big cat, baboon, vulture, flamingo; hyena exists), wildfire FX (large scale), call audio (144 clips x 2), rock shelter | XL |
| 4 Era 8 | Viking farm kit (longhouse, hall, boathouse), longship, Viking clothing set, rune stone, burial mound, hacksilver and scales, Thing site, lindorm legend asset | M |
| 5 Era 12 (A1) | Modern overlay: road, signs, ferry, cars, tourists, hiking gear, field-school dig site, museum interior, phone/camera props | M |
| 6 Eras 9, 11 | Stave church, overgrown-farm variants (9); gravel road, power house, pipe, pylons, steamer, early car, hotel (11) | M |
| 7 Eras 3-4 | A3 coast + cave, A4 valley + painted cave, Ice Age fauna (mammoth, woolly rhino, reindeer, horse, bison (exists), cave lion, cave bear (bear stand-in)), Homo sapiens Ice Age people, fat lamps, cave paint decals | L + L |

---

## 14. Slice 01: Era 10, Skarvik fjord village, 1850s

### 14.1 Scope
v1 section 9.1 unchanged (Skarvik valley ~2x2 km, 20 NPCs, 8 archetypes, 10 resources, 10 items, 5 buildings, 1 market, 1 trade route, weather, day/night, Singing Cavern, northern lights, save/load), set in autumn of an 1850s year, plus:
- **Fire**: player hearth at home, 1 outdoor campfire spot per 500 m of trail, flint and steel + tinder (birch bark, tinder fungus), firewood chain (v1 items: firewood bundle), banked hearth overnight, smokehouse and smithy run on fire, beacon cairn on the shoulder above the falls (lighting it brings the trader boat 1 day early, once per week; my call), matches as an import (base 30 skilling a box, my call).
- **Lore**: the 5 Era 10 lore entries in section 7.3 added to v1's 12 rumors (17 total).
- **Sea life**: seals, porpoises, herring shoal, basking shark (rare), orca (rare).
- **Legend sighting**: the fjord sea serpent (rules in 7.1).
- **Anchor stubs**: 6 hearth sockets, 4 cairn sockets and 5 carving rocks at A1 in their Era 10 default form; keepsake on the shelf; Long Map screen with A1 and one lit cell.
- Northern lights: lower from v1's 1 in 4 clear nights to 1 in 8 clear nights (my call: 61 N sees aurora less often than the north; ask).

### 14.2 Acceptance criteria
v1 section 9.2 blocks (Movement, Gather/craft/carry, Economy, NPCs, Dialogue and voice, Rumors and wonder, Building and growth, Survival, World) all stay, with the northern-lights check changed to 1 in 8. New blocks, each with an automated playthrough step (seeded bot):

**Fire**
- [ ] Light the home hearth with flint and steel and dry birch bark; catch rate over 200 bot sparks is 31.5% +- 7 (45% x 0.7, about 2 standard deviations).
- [ ] A camp fire with 10 kg branch wood in calm air burns 3 h 20 min in-game +- 5 min (3 kg/h).
- [ ] Heavy rain on an unsheltered camp fire at heat 60 holding 6 kg branch wood (target 61) loses about 20 heat/h net (rain -40, fuel pull +20) and reaches embers (below 10) in 2 h 30 min +- 10 min; a fire under the smokehouse roof loses no heat to rain.
- [ ] A banked hearth with 5 kg split logs is still revivable at 06:00 after banking at 22:00 (uses 4.6 kg, my calc).
- [ ] Revive from embers with dry fuel restores heat >= 15 at once; wet fuel cannot light from embers below heat 30.
- [ ] Sitting 1.5 m from a hearth at heat 60 indoors on a cold night gives Warmth +8.2/h +- 0.2 (unit test vs `tools/fire_calc.py`).
- [ ] Cooked fish gives 1.5x the Fullness of raw and +10 Warmth.
- [ ] Hardy preset: a full rainy cold night outdoors with no fire ends in a setback; with a small fire kept fed it does not.
- [ ] Each household hearth kept unbanked burns 20-25 kg logs per cold night (split logs, 23 kg calm, my calc); a 2-day cold snap drops village log stock and raises the log price toward 6.1 (v1 Chain B).
- [ ] No fire ever spreads to a building or tree (bot: 500 fires lit at random legal spots in wind 1.0).
- [ ] Matches appear at the stall only after a trader-boat call; 95% light rate in calm, 76% +- 5 in wind above 0.6 (95% x 0.8).
- [ ] Lighting the beacon cairn moves the next trader-boat arrival 1 day earlier, at most once per 7 days.
- [ ] Fire FX: hearth flame, smoke and light at 60 fps on High on the owner's phone; at most 4 fire lights active, none casting shadows.

**Lore, legends, traces**
- [ ] All 17 rumors/lore entries spread; the 5 Era 10 lore lines are voiced in every truth state they can take.
- [ ] Sea serpent sighting fires only when eligible (rumor held, Wayfinder >= Trusted, dusk, on the fjord shore); seeded 200-evening bot run: 2-6 sightings, never twice in one era.
- [ ] After a sighting, an exaggerated "the newcomer saw the serpent" rumor exists within 2 in-game days.
- [ ] Every trace socket at A1 shows its Era 10 default form; the H3 "giant's hearth" tale is told by at least one NPC.
- [ ] The keepsake is on the home shelf; picking it up adds it to the bag with its journal page.
- [ ] Sea life: seals haul out at low tide and leave the rocks when the player comes within 15 m.

### 14.3 NPC stress ladder
v1 section 9.3 unchanged.

### 14.4 Performance budget
v1 section 9.4 kept, updated with owner phone data (SM-S931B, 10-10): High at the spawn measured 70.4 fps, p95 19.4 ms, GPU 13.4 ms (build `e9b30bc`, before the speed fix `0194fd7`, which is verified on the laptop only). Rules added for fire (my call): at most 4 active fire lights (omni, no shadows) within 40 m, flames as a 64-particle flipbook per fire, smoke 32 particles, beyond 60 m a fire is an emissive card + glow only. Night with fire is the hero look and needs its own lighting preset (DESIGN 7.2 rule 6) tested on the phone before content work. Floor device still unknown (ask).

---

## 15. The five biggest design risks

| # | Risk | Why it matters | Mitigation |
|---|---|---|---|
| 1 | **Realistic hominin characters** | Eras 1-2 need a believable ape-like player and band at talk distance; no rigged free realistic sources are known to me. A doll-like hominin breaks the whole opening and the owner's realism bar | Start art R&D now (sculpt or commission one body, test on the phone) while Chapters 1-2 are built; do not schedule Chapter 3 until one body passes the owner's eye |
| 2 | **Scope: 12 eras, 4-5 anchors** | Even with A1 reused 7 times, this is several games of content | Chapters ship one at a time; A1 first; the Long Map makes a partial game whole; cut list ready: A5 (fold 6-7 into A1), Era 9 and 11 short |
| 3 | **Hunting and "no violence"** | The owner wants hunting; the game promises no violence; youth audience | Off-screen kills, player as tracker/driver, fishing and trapping shown; owner confirms (ask) |
| 4 | **Historical accuracy** | Many dates and readings here are unverified or debated (first fire, bipedal timing, early farming); semi-historic still needs to be right where it states facts | A fact sheet per era checked against sources before any line is voiced; in-game text says "people think" for debated claims; invented lore marked as such in the data |
| 5 | **Fun in the no-language eras** | Eras 1-2 drop trade, dialogue and prices, which carry v1's fun; calls and signs must carry the loop | Prototype Era 2's fire loop on the A1 terrain early (grey-box, no hominin art) and test whether keeping a fire through a night with predators circling is fun |

Also watching: era transitions feeling like level loads (time-lapse must be smooth on the phone); voice budget across 9 voiced eras (v1 estimated ~506 MB for 5 regions; per-era asset packs needed).

---

## 16. Calculations and sources

**My calcs**: `tools/fire_calc.py` (fuel per night, warmth cases, ember carrier life); `tools/econ_calc.py` (v1 prices, unchanged). Bot acceptance numbers in 14.2 are derived from the 6.3-6.5 rules (my calc).

**Checked this session (web sources, 2026-10-10)**:
- Wonderwerk Cave controlled fire ~1 Mya, PNAS 2012, debated: https://www.sciencenews.org/article/ashes-oldest-controlled-fire
- Lomekwi 3 stone tools 3.3 Mya, West Turkana, Kenya: https://en.wikipedia.org/wiki/Lomekwi
- Makapansgat pebble ~3 Mya, ~32 km from source, carried-face reading is a hypothesis: https://en.wikipedia.org/wiki/Makapansgat_pebble
- Blombos Cave shell beads and engraved ochre ~75,000 years: https://www.scientificamerican.com/article/ancient-shells-may-be-ear
- Fosna/Komsa first coastal settlement of Norway ~9500-8000 BC: https://en.wikipedia.org/wiki/Komsa_culture , https://ntnuopen.ntnu.no/ntnu-xmlui/handle/11250/2496980
- Funnel Beaker ~4000 BC in Norway, farming important from ~2450-2350 BC: https://sciencenorway.no/archaeology-forskningno-history/first-stone-age-farmers-in-norway-gave-up-after-short-period-of-time/1460827
- Pontoppidan's Natural History of Norway 1752-53 (sea serpent, kraken); Konungs skuggsja c. 1250; hafgufa in Orvar-Odds saga: https://en.wikipedia.org/wiki/Erik_Pontoppidan , https://blog.biodiversitylibrary.org/2014/10/release-kraken.html
- Naeroyfjord UNESCO 2005; Njardarheimr Viking village at Gudvangen: https://exarc.net/members/venues/viking-valley-no
- Selma, Lake Seljord, first written account 1750: https://en.wikipedia.org/wiki/Selma_(lake_monster)
- Tyssedal hydropower from 1906, Odda carbide from 1908: https://en.wikipedia.org/wiki/Tyssedal_Hydroelectric_Power_Station
- Black Death in Bergen 1349 by ship; Hanseatic Kontor at Bryggen ~1360: https://thehiddennorth.com/the-hanseatic-league-bergen/

Not found by my searches: the Laetoli footprint date, the Flam Railway opening year, fossegrim details. All three are marked (unverified) or left out.

---

## 17. Open questions for the owner
1. **Hunting**: is "the player tracks and drives, the kill is off screen" right, or should hunting be left out (fishing, trapping, gathering only)?
2. **Dragons**: should a dragon or sea serpent ever be confirmed as real in the world, or stay a rare, unconfirmed sighting (my default)?
3. **Speech before English**: invented tongue with subtitles in Eras 3-4 and English from Era 5 (my pick), or English everywhere from Era 3?
4. **Wordless calls in Eras 1-2**: who or what provides the call sounds (your own recordings, licensed primate/human sound libraries, a voice actor)?
5. **One protagonist or a choice**: per era, pick a girl or boy of the line (doubles character art and voice), or one fixed character per era?
6. **A5 Jaeren**: keep a fifth anchor for farming and Bronze Age, or fold Eras 6-7 into the fjord (cheaper, less variety)?
7. **Kefalonia and Wadi Rum drafts**: keep Wadi Rum as the Era 3 walk north and Kefalonia as an optional Bronze Age voyage, or drop both?
8. **Release order**: build order starts at Era 10, but players should start at Era 1. Is a public "Era 10 alone" release fine as an early test, or nothing public until Era 1 exists?
9. **Northern lights at 61 N**: 1 in 8 clear nights (my call) or keep v1's 1 in 4 for wonder's sake?
10. Still open from v1: youth age band, floor phone, voice source, name (v1 names were for a trade game; a time-spanning game needs new ones).
