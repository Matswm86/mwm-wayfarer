# MWM Wayfarer (working title): owner brief, 2026-10-07

## What the owner asked for
A new Android game. Open world, exploration and wondrous marvel. Graphics at the same level as, or better than, MWM Race Riders (`~/MWM/projects/mwm-race-riders/`, realistic scanned-CC0 look). Characters/NPCs with English lines and voices. Skyrim / Assassin's Creed feel and movement (third person, smooth locomotion, climbing, swimming), but NO violence. For youth and adults. Themes: building, exploration, gathering, surviving, selling/buying, import/export, trade, community.

## Owner decisions (2026-10-07)
- Engine: undecided until the art drafts are seen (Godot 4.6 vs Unity 6). Write design docs engine-neutral.
- NPC dialogue: pre-written + pre-voiced. Lines authored at dev time (by Claude, from simulation facts and templates), voiced by local TTS at build time, cached as audio. No live LLM in the shipped game, works fully offline, no API cost.
- The game spans SEVERAL different-looking worlds/regions (not one biome). Drafts show 2-3 candidate settings; the full game links 4-6 regions through trade routes.
- Look: modern, realistic, high-end. No toy/cartoon look (owner rejected Race Riders v1 for that). No purple in UI chrome.

## Outside feedback notes the owner wants considered (condensed)
- Core fantasy: a living beautiful world where the player explores, discovers resources and wonders, builds a life, meets believable characters, joins communities and becomes economically/socially important. Loop: explore → discover → gather → learn → trade → build → connect → unlock → explore further. Not kill → loot → level.
- NPC AI in layers: (1) deterministic game AI: needs (hunger, energy, social, safety), schedule (wake, work, eat, socialize, sleep), goals, behaviours; (2) personality + preferences + relationships as data; (3) dialogue expresses simulation facts, never invents world facts.
- Semantic NPC memories (event, importance, relationship change, timestamp), not transcripts. NPCs remember help, trades, absences.
- World simulation where systems chain: rain → river rises → boats slower → fish population → fish prices → merchants → fishermen → player opportunity.
- Economy layers: player (gather → process → craft → sell → invest → build), local (villages specialise: wood, grain, textiles), regional (roads, boats, caravans, markets, warehouses, ports). Player roles: farmer, builder, merchant, explorer, shipper, artisan, innkeeper, trader, collector, architect, community leader.
- Wonders as a progression system (example names: Singing Cavern, Glass Forest, Sky Bridge, Forgotten Observatory, Bluewater Falls, Whale Graveyard, Floating Isles, northern lights, meteor showers, seasonal flowers). Not all on the map: rumors lead to them.
- Rumors: true, partly true, outdated, exaggerated, false. Talking is part of exploring.
- Reputation per village / merchant / craft / explorer / community, not good/evil.
- Building physically changes the simulation (timber → foundation → walls → roof → NPC moves in → shop opens). Settlements grow in stages (population 43 → 71 → 132, new market, dock, guild, festival).
- Data-driven: NPC/Item/Building/Quest/Biome/Resource/TradeRoute/Dialogue/WorldEvent definitions, never hard-coded per NPC.
- NPC LOD: near = full AI + animation, 100 m = low-frequency AI, 2 km = statistical, other region = abstract daily tick.
- Animation matters as much as graphics: walking an empty field must feel good (accel/decel, turns, slopes, stairs, jump, climb, swim, sit, pick up, harvest, carry, place, talk, ride, gestures).
- Mobile first: 60 fps high-end, 30 fps floor; budget CPU/GPU/RAM/battery/thermals/draw calls/GC from day one.
- Start small: Vertical slice 01 = one valley, 1 village, 20 NPCs, forest, river, mountain, 10 resources, 10 items, 5 buildings, 1 market, 1 trade route, weather, day/night; walk/run/jump/gather/craft/build/sell/buy/talk/explore/sleep/save; one mysterious location. Then stress-test NPC counts 20→50→100→250→500.
- "AAA-feeling systems in an AA-sized world": a 2x2 km world with depth beats a 50 km² empty map.
- Every feature gets acceptance criteria (checkbox list) and an automated playthrough test.

## Orientation
Landscape 1920x1080 (third-person open world), a deliberate break from the studio's portrait default.
