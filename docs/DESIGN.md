# MWM Wayfarer: visual design spec

Owner: graphic-designer. Version 1, 2026-10-10. The builder reads this before touching any colour, font, light or UI node. Every rule has its reason next to it. Engine-neutral where possible; Godot names are given where the studio default (Godot 4.6/4.7, Mobile renderer) applies.

Contrast numbers are WCAG 2.x ratios **(my calc)** from `tools/art/wf_ui.py` (`contrast()`), printed each time `tools/art/ui_screens.py` draws a screen.

Mockups this spec is drawn from (all 1920x1080 landscape, in `docs/mockups/`):

| File | What it shows | State |
|---|---|---|
| `key_fjord_real_terrain.jpg` | Approved world frame: Skarvik Fjord on real Kartverket terrain, day light set | Approved look reference (10-10) |
| `key_fjord_rock.jpg` | Same frame after the rock pass (10-10 b): gneiss walls, far gullies, neutral sun, fog 0.22 | Proposed replacement for the reference (designer verdict: passes; owner sign-off owed) |
| `key_archipelago_terraces.jpg` | Kefalonia from the slope above the headland: terraces with dry-stone risers and olive rows, bay, layered far coast | Improved; still below bar in the bare foreground and the pale far coast |
| `key_canyon_siq.jpg` | Redwall Oasis from inside the siq: sunlit strata wall, warm bounce, sky strip | Passes as direction; walls a little too clean (more Antelope Canyon than Wadi Rum) |
| `ui_hud.jpg` | Exploring HUD on the rock-pass fjord key | Matches this spec (type redrawn 10-10 b) |
| `ui_trade.jpg` | Skarvik market, Sell tab | Matches this spec |
| `ui_wonder.jpg` | Wonder discovery card, the Singing Cavern | Matches this spec; the vista is a 2D composite stand-in |
| `ui_talk.jpg` | Talk to Ingrid (fisher), GDD 6.4 line, Ingrid rendered (MakeHuman stand-in) | Matches this spec (10-10 b); face is a stand-in, not shippable |
| `build_draft.jpg` | Build mode on the rock-pass fjord | Type matches this spec (10-10 b); the ghost sits on the shore path, move it onto the meadow in the next pass |

---

## 1. Visual theme

**Mood:** a real place on a clear day, quiet and wide, with people in it. Calm light, honest materials, long views. Wonder comes from scale and light, never from glow effects.

**Tier:** premium 3D, **realistic variant** (owner, 2026-10-07: "modern, realistic, high-end, no toy or cartoon look"). This overrides the template's "stylized, never photoreal" line for this game only. Everything else in section 10 (hero scene first, phone budget, four questions) applies.

**References (what to take, not what to copy):**
- **Assassin's Creed Odyssey / Valhalla (Ubisoft):** daylight landscapes lit by one strong sun with a matching sky, aerial perspective that stays light (far ridges go blue-grey, not milky white), and a minimal HUD that disappears while you walk. Take the light logic and the HUD restraint; leave the combat UI.
- **Kingdom Come: Deliverance (Warhorse):** believable villages built from real materials (timber, turf, stone, mud), people dressed for work, no fantasy colour. Take the material honesty and the "lived-in" props; leave the dark menus.
- **MWM Race Riders** (`~/MWM/projects/mwm-race-riders/`, ref `docs/mockups/racerriders_ref.jpg`): the studio's own bar for scanned CC0 assets on a phone. Wayfarer must meet or beat it.

**Not this:** saturated toy colours, outlines, cel shading, bloom halos, lens dirt, purple-blue "magic" gradients in UI, glassmorphism stacks.

## 2. Palette

### 2.1 UI tokens
Source of truth: `tools/art/wf_ui.py`. Change a value there and here together.

| Token | Hex | Godot Color | Use | Why / measured |
|---|---|---|---|---|
| `ink` | #11151A | Color(0.067, 0.082, 0.102) | Dark panels over the world (HUD chips, talk, replies) at **0.80-0.88 alpha** | Neutral near-black, no blue tint, so it never reads as "night mode" |
| `ink2` | #1E242B | Color(0.118, 0.141, 0.169) | Raised dark surface (pressed state, dark tooltips) | |
| `paper` | #F5F0E6 | Color(0.961, 0.941, 0.902) | Light panels: market ledger, wonder card, journal, bag, map | Light by default (studio rule); warm paper reads as an object in the world, not an app sheet |
| `paper2` | #E8E0D2 | Color(0.910, 0.878, 0.824) | Row stripes, segmented-control track, dividers on paper | |
| `text_d` | #F6F3EC | Color(0.965, 0.953, 0.925) | Text on ink | 12.17:1 on ink 88% over bright sky; 10.31:1 on ink 84% over pure white |
| `muted_d` | #B8BFC7 | Color(0.722, 0.749, 0.780) | Secondary text on ink | 7.27:1 on ink 88% over sky; **3.73:1 on ink 62%: fails**, hence the 0.80 alpha floor |
| `text_l` | #1B1F24 | Color(0.106, 0.122, 0.141) | Text on paper; dark primary button fill | 14.58:1 on paper, 12.64:1 on paper2 |
| `muted_l` | #5C564E | Color(0.361, 0.337, 0.306) | Secondary text on paper | 6.38:1 on paper, 5.53:1 on paper2 |
| `amber` | #F0A83C | Color(0.941, 0.659, 0.235) | **Wonders, rumors, discovery**; speaker names; the context Action button | 6.66:1 on ink 88% over sky; ink on amber 9.05:1 |
| `amber_d` | #825410 | Color(0.510, 0.329, 0.063) | Amber text on paper ("Wonder found", rumor rewards) | 5.73:1 on paper, 4.97:1 on paper2 (old #966014 was 4.03 on paper2: fixed 10-10) |
| `teal` | #2FA396 | Color(0.184, 0.639, 0.588) | Fills and icons only: valid placement, progress bars, checkmarks | 5.93:1 on solid ink; **4.37:1 on ink 88% over sky: not for text** |
| `teal_l` | #48BAAC | Color(0.282, 0.729, 0.675) | Teal **text** on dark panels (relationship band) | 5.71:1 on ink 88% over sky (added 10-10) |
| `teal_d` | #146E64 | Color(0.078, 0.431, 0.392) | **Trade and confirm**: primary commerce button fill; "price high" text on paper | white on it 6.10:1; 5.37:1 on paper, 5.13:1 on the selected-row tint |
| `clay` | #E06650 | Color(0.878, 0.400, 0.314) | Missing material, "can't do this" icons on ink | 5.40:1 on solid ink (old #D2553F was 4.46: fixed 10-10). 2.99:1 on paper: never on paper |
| `clay_d` | #A83422 | Color(0.659, 0.204, 0.133) | "Price low" and warnings as text on paper | 5.82:1 on paper, 5.04:1 on paper2. 2.77:1 on ink: never on ink |
| `select_tint` | #E2EEEA | Color(0.886, 0.933, 0.918) | Selected row fill on paper, with a 4 px `teal_d` outline | |
| `coin` | #D6A034 / ring #FAD678 | Color(0.839, 0.627, 0.204) | Coin glyph only, never text | |

**Split 60 / 30 / 10.** 60 = the world itself (the scene is the background of every screen; panels never cover more than about 70% of it except full-screen journal/map). 30 = UI surfaces (`ink` over the world while moving, `paper` when the player stops to read or decide). 10 = accents, with fixed meanings:
- **amber = wonder and curiosity** (wonders, rumors, the Action button, who is speaking),
- **teal = trade and yes** (sell/buy, confirm, valid, price in your favour),
- **clay = missing or against you** (lacking material, price low when selling).
Never swap these meanings; a player learns them in the first ten minutes.

**No purple** anywhere in UI chrome (owner). The aurora in the world (`#7FD6A6` green, with natural magenta fringes) is play content and allowed.

### 2.2 Region palettes (world, play content)
From `tools/art/palettes.py`. Fjord, archipelago and canyon were measured from key frames then rounded by role; delta and highlands are designed (no render yet). Order = 60, 60, 30, 30, accent, accent.

| Region | Swatches | Roles |
|---|---|---|
| R1 Skarvik Fjord | #1C2B2E #3F4C4A #5E7044 #8A2E22 #E3B27A #7FD6A6 | shadow water, wet rock, turf, falu red, lamp light, aurora |
| R2 Amberline Isles | #F1ECE0 #CFC3A8 #7E8A5A #1FB3B0 #0B6E8C #E8A85C | limestone, dry grass, olive, shallows, deep sea, late sun |
| R3 Redwall Oasis | #7A3A24 #B5653E #D9A273 #4F6B3A #24476E #E9DCC6 | deep strata, sandstone, sand, palm, indigo awning, linen |
| R4 Greenmouth Delta | #13261C #2F5530 #6E8C3A #6B5A3A #3E7F86 #E7C45A | canopy shadow, leaf, moss light, mud bank, river, flower gold |
| R5 Frostspine Highlands | #E9EEF2 #A9C4D6 #4F7A99 #3A3F44 #8C8F86 #D97B4A | snow, ice, crevasse blue, basalt, moraine, hut red |

UI tokens do **not** change per region. Only the world does. (Studio rule: one look per game, consistent inside it.)

## 3. Typography

Fonts live in `assets/fonts/`, both **SIL Open Font License 1.1** (licence texts beside them: `Inter-OFL.txt`, `SourceSerif4-OFL.txt`). OFL allows bundling in a commercial app; keep the licence files in the build and list them in CREDITS.

- **Inter** (variable, `Inter[opsz,wght].ttf`): all UI text, numbers, buttons. Tabular figures for prices (`tnum`) so columns line up.
- **Source Serif 4** (variable, roman + italic): place names, item names on cards, wonder titles, journal and lore text. The serif is the "world" voice; the sans is the "tool" voice.

Scale. The mock is 1920x1080 = 2.625 px per dp on a 411 dp tall phone. Sizes in px at 1080 tall (sp = px / 2.625):

| Role | Font | px | sp | Weight | Used for |
|---|---|---|---|---|---|
| Display | Source Serif 4 | 64-68 | 24-26 | 700 | Wonder name, region arrival |
| Title | Source Serif 4 (cards) / Inter (names) | 48-56 | 18-21 | 700 | Market name, item name on a card, speaker name |
| Body | Inter | **40** (floor) | 15 | 500-600 | Rows, NPC lines (42), replies (38-40), lore (38 serif italic) |
| Number | Inter | 44 | 17 | 700 | Prices, counts, coins |
| Label | Inter | 34 | 13 | 500 | Secondary lines, explanations |
| Caption / caps | Inter | **32** (floor), caps 28 with 8% tracking | 12 | 500 / 700 | Reasons, kg, column heads |

Hard floor: **no text below 32 px** (12 sp) on screens the player reads (cards, talk, trade), and **nothing below 28 px anywhere**, HUD included (owner 10-10). The only 28-30 px text: caps labels with 8% tracking and weight 700 (column heads, "BUILD") and the compass NE/NW letters (bold). Body never below 40 px. Every text-carrying chip or panel over the world sits at **0.84 alpha** or more.

**HUD and build-mode scale** (redrawn 10-10 b; was 15-24 px):

| HUD element | Font | px | sp | Weight |
|---|---|---|---|---|
| Compass N/E/S/W | Inter | 40 | 15 | 700 |
| Compass NE/NW/SE/SW | Inter | 30 | 11 | 700, `muted_d`; hidden when a marker icon sits within 9 deg |
| Compass marker label ("Bluewater Falls 1.2 km") | Inter | 32 | 12 | 600, pill 52 tall; neighbours alternate two rows so labels never overlap |
| Time/weather chip, pack chip | Inter | 36 | 14 | 600, chips 72 and 92 tall, 400 wide |
| Action button label ("Gather") | Inter | 32 | 12 | 700, `ink` on `amber` |
| World prompt ("Cloudberries x6") | Inter | 34 | 13 | 600, pill 64 tall |
| Build banner: caps / title / sub-line | Inter | 28 caps / 44 / 34 | 11 / 17 / 13 | 700 / 700 / 500 (`muted_d`) |
| Build material chips, hint line, "Place frame" | Inter | 36 / 34 / 32 | 14 / 13 / 12 | 600 / 500 / 700 |

Wording: plain words, short sentences, no jargon. "You get each", not "Unit price". "74% high", not "+74% Δ". "Ingrid remembers: you paid fair for her herring", not "Affinity +5". Numbers carry units (kg, coins, km).

## 4. Components

All sizes in px at 1920x1080. Hit areas are **at least 130 px** (48 dp = 126 px, rounded up) with **at least 18 px** between neighbouring targets. Visible shape may equal the hit area (mocks do) or sit inside it.

### 4.1 Dark chip and panel (over the world, while moving)
- Fill `ink` at **0.80-0.88 alpha**. Never below 0.80 when it carries text (muted text fails below that over bright sky).
- Radius = half the height for chips and pills; 28 for panels. No border. No blur-behind (cost, section 10).
- Drop shadow only on panels that float over bright scenery: 18 px blur, 0.35 alpha, 6 px down.

### 4.2 Paper panel (when the player stops: trade, wonder, journal, bag, map)
- Fill `paper` at 0.98, radius 28-30, shadow as above. World behind is blurred 2-14 px and dimmed 18-50% so the panel wins.
- Rows 140-146 tall, stripes alternate `paper` / `paper2`, inset 22 px, radius 20.
- Selected row: `select_tint` + 4 px `teal_d` outline.

### 4.3 Buttons
| Kind | Size | Fill / label | Where |
|---|---|---|---|
| Primary commerce | full card width x 144, pill | `teal_d` / white Inter 44 bold, coin glyph before the amount | Trade "Sell 12 for 104", talk "I have smoked fish to sell" |
| Primary neutral | 380 x 144, pill | `text_l` / `paper` Inter 44 bold | Wonder "Continue" |
| Secondary | min 130 tall, pill | 4 px `text_l` outline on paper, or `ink` 0.88 on the world | "Read in journal", replies, "All" |
| Round icon | 130 dia | `ink` 0.84, white glyph 40-60 px | Close, map, settings, rotate |
| Action (context) | 190 dia | `amber`, 4 px white ring, `ink` glyph + label | HUD: Gather / Talk / Build (GDD 7) |
| Stepper | 130 dia circles, count between in Inter 64 bold | 4 px outline | Trade quantity |
| Segmented control | 130 tall track `paper2`, active segment `text_l` with `paper` label | | Buy / Sell |

Pressed state: scale to 0.96 and darken fill 12% for 0.08 s, release 0.15 s ease-out. Disabled: 40% opacity plus a one-line reason underneath (never a silent grey button).

### 4.4 Trade screen (`ui_trade.jpg`)
- Ledger left (48..1236), action card right (1268..1872), wallet chip + Close top right. The world stays visible top right.
- Row = icon 120x104, name (body), **reason** (caption, `muted_l`): the live sim fact behind the price ("River flood: no fresh fish for 2 days"). This is GDD pillar P1 made visible; never drop the reason line.
- Price column = what **you** get (Sell tab) or pay (Buy tab), with "N% high / low / normal" against the base price: `teal_d` when it favours the player, `clay_d` when it does not.
- Action card: item, one plain sentence on why the price is what it is (max 2 lines), stepper + All, then the primary button with the total. Primary button is bottom-right, in the right thumb's rest spot.
- Weights shown per row (total kg) must add up to the pack chip.

### 4.5 Wonder discovery card (`ui_wonder.jpg`)
- Centred paper card 1680 x 936 over the blurred, dimmed world.
- Left: vista 860 x 520 in a 12 px photo mat (the journal illustration), serif italic caption under it.
- Right: amber diamond + "WONDER FOUND" (`amber_d` caps), count "1 of 30", name in Display serif, region in label, 2-3 lines of lore in serif italic.
- Bottom: "What you get" list, 2 columns, icon + text: material, Wayfinder reputation, cairn, next rumor (amber_d). Max 4 rewards.
- Buttons: "Read in journal" (secondary) above "Continue" (primary), both bottom right.
- In game the vista is a real capture from the wonder's authored viewpoint, not a 2D composite.

### 4.6 Talk screen (`ui_talk.jpg`)
- Camera frames the NPC waist-up in the upper middle third (between x 560 and 1000 at 1080p); the subtitle panel and replies never cover the face.
- Subtitle panel bottom-left (48..1130, 700..1032), `ink` 0.88: speaker name (`amber`, Inter 48 bold), role (`muted_d`), relationship band as an outline pill (`teal_l`), voice waveform glyph, the line at 42 px (max 2 lines; split longer lines into two beats), then a divider and **one memory or fact line** in `muted_d` ("She remembers: you paid fair for her herring, day 3").
- Replies: right column, 4 max, each 130 tall with 18 px gaps, bottom-aligned so the most likely reply sits under the right thumb. The commerce reply is `teal_d` filled; rumor replies carry an amber speech glyph; Goodbye is always last with an X.
- Text is exactly the pre-voiced line (GDD 6). No typewriter effect: show the whole line at once while the audio plays.

### 4.7 Bars and meters
- Pack weight bar: 6 px track white 24% alpha, `teal` fill, turns `clay` above 90%.
- Warmth / Fullness / Rest: hidden above 50 (GDD 7); below, a 130 px chip with icon + number, `clay` icon below 25.
- Stamina: a ring around the character (world space), not on the HUD.

### 4.8 HUD (`ui_hud.jpg`), fixed 10-10 b
1. Type per the HUD table in section 3; every chip `ink` at 0.84 (`HUD_A` in `ui_screens.py`).
2. Compass 940 x 76, top centre, 40 px from the top. Markers: amber diamond = wonder, white speech bubble = rumor, `teal_l` anchor = trade. Labels hang under the bar on two alternating rows.
3. `build_draft.jpg` redrawn on the real-terrain `build` render (10-10 b).

## 5. Layout

- Landscape 1920 x 1080 (owner). Safe margin **48 px** on all sides; also respect the device cutout insets (Godot `DisplayServer.get_display_safe_area()`), whichever is larger.
- Thumb zones (GDD 7): left thumb = move stick anywhere in x 0-800, y 300-1080; right thumb = camera drag plus buttons in the bottom-right quarter. **Primary actions go bottom right** on every screen (Action, Sell, Continue, the commerce reply).
- Reading zone = top and middle of the screen, left of centre. Long text sits in the bottom-left panel (talk) or on paper (cards), never under the right thumb.
- HUD while exploring: compass top centre, menu + map top left, time/weather + pack top right, stick bottom left, Action/Traverse/Drop bottom right. Nothing in the centre third: that is where the world is.
- Full-screen panels (bag, map, journal) pause the game (GDD 7) and keep a 48 px strip of the blurred world visible at the edges so the player never loses the place.

## 6. Depth and motion

- Shadows: one soft drop shadow per floating panel (section 4.1). No inner shadows, no bevels, no glows on UI.
- Tweens: UI 0.15-0.25 s ease-out; panels slide 24 px + fade in 0.2 s; the wonder card fades the world to blur over 0.6 s first (let the vista land), then the card rises in 0.3 s.
- Wonder moment: 2 s of free camera on the vista with HUD hidden and a single low chord, **then** the card. No confetti, no screen shake, no flashing.
- Screen shake: none in UI. Heavy landing (GDD 4) may use a 0.15 s, 4 px camera dip, nothing more.
- Numbers that change (coins, price after a sale) count up over 0.4 s.

## 7. Game art

### 7.1 Art direction by region
All regions share: scanned or photo-sourced CC0 materials, real-world scale (doors 2.1 m, steps 18 cm), one sun, physically plausible sky. Each region differs by geology, vegetation, building material, water colour and light quality.

| Region | Terrain | Water | Buildings | Vegetation | Light |
|---|---|---|---|---|---|
| **R1 Skarvik Fjord** | Real elevation (Kartverket DTM 10, Naeroyfjord), granite/gneiss walls 50-70 deg with benches, scree aprons. **Rock pass 10-10 b:** faces steeper than about 48 deg are dark grey gneiss (albedo 0.18-0.32, never beige), one scan at two scales (40 m + 7 m, the 7 m grain only within 350-900 m of the camera), vertical seep streaks, olive lichen; a darker glossy wet band 0-3 m above the water; snow only on flatter ground above about 1250 m; beyond 1.5 km the tiled scans fade to flat forest green (gentle slopes) and grey (steep), broken by a 300 m noise; from 400 m out, steep faces get rockfall chutes (noise stretched 8x along Z, as bump + darkening); terrain specular 0.12 and roughness 1.0 far (grazing sky reflections had turned far slopes white) | Deep blue-green to clear brown-green shallows, mirror-calm reflections of the walls | Dark-tarred and falu-red timber, turf roofs, stone footings, wooden pier | Birch and pine below 500 m, dense; heather, cloudberry bog; bare rock above | High-latitude sun 25-35 deg, long soft shadows, cool fill from the sky |
| **R2 Amberline Isles** | Limestone islands, terraces, sea caves, a natural arch. Olive terraces = 3 m steps with steep 0.4 m-deep dry-stone risers (stone-wall scan) and soil treads, olives in rows mid-tread; terrace fields need ground at 0.6 m resolution or the risers vanish | Turquoise shallows over sand, deep cobalt off the shelf | White limestone, older marble ruins half buried | Olive, cypress, dry gold grass, figs | Hard Mediterranean sun 45-60 deg, short dark shadows, bright bounce |
| **R3 Redwall Oasis** | Red sandstone slot canyons, cliff dwellings, layered strata. **The siq (slot) is the region's signature view:** 5-10 m floor, 60 m walls that lean apart towards a sky strip, built as wall meshes (not heightfield), rounded ledges every 2-3 m, colour bands deep red #6E3020 / #8E3E26, sandstone #B5653E / #C47A50, ochre #D9A273, cream #E6C9A2, rose #B0604A | Small green pools in the oasis only | Mud brick and sandstone, indigo awnings, caravanserai courtyards | Date palms, low scrub | Strong warm sun, deep cool shadows in slots; night = huge star field |
| **R4 Greenmouth Delta** | Flat channels, mud banks, buttress roots | Wide brown-green, slow, misty | Stilt houses of hardwood and reed | Mangroves, giant trees, ferns; glowing fungi at night | Diffuse humid light, mist in the morning (the one region allowed denser fog, 0.45 max) |
| **R5 Frostspine Highlands** | Glacier tongues, moraines, terraced barley | Meltwater, hot springs steaming | Stone and felt huts, cairns | Barley, moss, sparse juniper | Thin, bright, blue-white light; snow glare kept under control by exposure |

Terrain from real elevation data wherever the licence allows (section 7.4). A heightfield cannot draw a near-vertical face: use rock scan meshes on true cliff bands (above about 70 deg), not stretched heightfield textures (10-10 lesson: stretched cells give vertical streaks). Features narrower than the data (a 5 m slot in 30 m data) are authored meshes laid into the real relief.

**Four questions, answered for the 10-10 b additions**
- *Fjord rock pass:* 1) yes, the walls fill half of every fjord frame; 2) one splat shader, triplanar on the steep layer only, plus three world-space masks (streaks, wet band, snow) = a few ALU ops, no extra textures beyond the second scan sample; 3) the far fade is itself the cheap trick (it removes texture work past 1.5 km); 4) fits. Verdict: ship it, with the 7 m grain sample skipped on the floor tier.
- *Siq walls:* 1) yes, it is the region's key view; 2) two wall meshes at 1 m spacing in game (about 40k triangles each, LOD 2 m past 60 m), one material, no transparency; 3) strata are geometry, not a parallax shader: cheaper on the Mobile renderer; 4) fits.
- *Terrace fields:* 1) yes at 30-300 m; 2) 0.6 m ground only inside the two field ellipses, coarse terrain elsewhere; in game bake the risers into the heightmap at 0.5 m and use one stone-wall layer; 3) beyond 300 m the stone bands could be a painted macro texture; 4) fits.

### 7.2 Lighting rules (learned 2026-10-10 on the fjord key)
1. **The sun must reach the scene.** In a fjord or canyon, the sun elevation has to clear the walls: 30 deg on the fjord key. At 7 deg nothing received direct light and the frame went flat.
2. **Daytime HDRI matched to the sun.** Use a clear or partly cloudy daytime sky (`kloofendal_48d_partly_cloudy_puresky`) whose sun direction and colour agree with the key light. **Never put a dusk HDRI with a high sun**: the 10-10 test gave a black sky hole that the fog had been hiding.
3. **Light fog:** depth fog starting at **about 200 m**, maximum density **0.22** on the fjord (was 0.3: it laid a milky sheet over every wall past 3 km, 10-10 b probe). Mist cards at alpha 0.15 at most. Fog is for distance, not for hiding missing detail; the 0.7 fog and four 0.4 mist cards washed the old frame out.
4. **Exposure 0**, no auto-exposure jumps; grade only after lighting and materials stop improving (refmatch, section 10).
5. Water needs real reflections of the walls (reflection probe or a cheap planar on the phone, section 10), not probe-only grey.
6. Dusk, night and aurora are separate presets with their own HDRI, sun below 5 deg, moon key and lantern accents. Test each preset on its own; never mix day sky with night light.
7. **Sun colour follows sun height.** A 30 deg morning sun is near white, `(1.0, 0.90, 0.78)`; the old golden-hour `(1.0, 0.66, 0.36)` turned every sunlit face beige (10-10 b) and is only for suns below about 12 deg (`WF_SUN_WARM=1`).
8. **Aerial perspective is not fog.** Within 2 km keep fog at 0.3 or less. Past 3 km the haze may reach about 0.36 with quadratic falloff, blue-grey `(0.62, 0.74, 0.90)`, never milky white, so headlands separate into layers (archipelago 10-10 b: start 250 m, depth 5200 m, max 0.36). The compositor mixes fog in linear light, so 0.3 already reads as a heavy veil after the view transform.
9. **Slots and canyons:** sun high (about 74 deg) and across the slot so it lands on the upper wall; sky fill low (HDRI 0.45) so the shadow wall glows with warm bounce instead of going grey-blue.
10. The look-dev overrides live as env vars in `tools/art/scene_fjord.py` (`WF_SUN_ELEV`, `WF_SUN_ENERGY`, `WF_FOG_START`, `WF_FOG_MAX`, `WF_MIST_ALPHA`, `WF_EXPOSURE`, `WF_HDRI`, `WF_DEM`, `WF_YAW`). The approved set: `WF_DEM=1 WF_YAW=-10`, sun 30 deg, fog 200 / 0.22 (10-10 b), mist 0.15, exposure 0, kloofendal HDRI.

### 7.3 Characters and props
- Realistic proportions, work clothes in natural dyes (wool grey, oilskin yellow, linen, falu red); no bright synthetic colours on NPCs.
- Faces must read at talk-camera distance (waist-up, 3.5-4 m with a 60 mm lens). MakeHuman (MPFB, CC0) was the stand-in and is retired by pass 2 (10-10 c): the player, Luca, is a scanned human (Renderpeople scan, albedo 2K in the game), Ingrid a realistic woman in denim work bibs, linen shirt and boots (section 7.6). Both share one animation set retargeted from Quaternius UAL (CC0): idle, walk, run, sprint, talk, interact, pickup, sit.
- Hero budget (owner 10-10, frame time is the only limit): player up to about 60k triangles with 4K albedo; NPCs at talk distance up to 60k with 4K; crowd NPCs 15-25k with 2K.
- **Ingrid** (`wf_mh.py` preset `ingrid`, 10-10 b): woman about 50, long mid-brown hair (a ponytail read as a man from the front), orange oilskin bibs over a grey-blue wool shirt, texture eyes (the procedural MPFB eyes glow at talk distance), calm talk pose `talk_calm` (hands low, no wide gesture). Talk camera: over the player's left shoulder, NPC face at x about 660 px, y about 400 px at 1080p, player blurred under the replies.
- Item icons: render each item model in the game's own daylight on transparent, 256 px, three-quarter view, consistent light from top-left (`tools/art/icons.py`). The trade mock uses Poly Haven's own CC0 thumbnails as stand-ins.
- Textures (raised by the owner 10-10: APK size is no constraint): characters 4K, cliff materials 4K, rock meshes 2-4K, trees 2K atlases, props 2K, small props 1K. ASTC on Android. Atlas small props.

### 7.4 Sources
Poly Haven (CC0: models, textures, HDRIs), Blender Studio Human Base Meshes (CC0), MakeHuman system assets (CC0), Kartverket DTM (CC BY 4.0), Copernicus GLO-30 for Kefalonia and Wadi Rum (licence verified 10-10: free, distribution allowed, the credit text in `assets/_raw/dem/cop30/SOURCE.md` is required). Every new source goes into CREDITS (section 11) the day it is added.
Added 10-10 c: ambientCG (CC0 materials), Quaternius Universal Animation Library (CC0 animations), Sketchfab models under CC BY 4.0 (author credit required; each listed in the asset's `NOTES.md`). Owner decision 10-10: licence does not block use of a free asset that looks good (NC included); record the licence anyway and re-check before any paid release.

### 7.5 Animals (wildlife only, GDD line 32)
- Realistic scanned-look or hand-sculpted models with real proportions and fur textures; rigged with at least walk, run, idle/graze. **No stylized, low-poly, cel-shaded or anthropomorphic packs.**
- Licence: superseded by the owner 10-10 (17:12): free assets of any licence may be used, NC included; record author, URL, licence and date in `assets/_raw/animals/<species>/CREDITS.md` and re-check before any paid release. Tripo free-tier output stays out (Tripo keeps the rights).
- Phone budget: 8-20k triangles per animal, one 2048 texture, at most 6 full animals near the camera, impostors or culling beyond 80 m.
- 10-10 b shortlist (licence checked through the Sketchfab API, not yet downloaded: needs a Sketchfab login):

| Species | Model | Author | Licence | Tris / clips | Verdict |
|---|---|---|---|---|---|
| Red deer (stand-in) | Realistic Animated Elk 3D Model (wapiti, the red deer's closest relative) `787834f9caa2474d9f1814b807c072d7` | WildMesh 3D | CC BY 4.0 | 7.9k / 53 | Best realistic rigged cervid found; author notes "known rigging problems" in this older version |
| Red deer (alt) | Animated Deer `4cff1e63f4e941198b3d56300b3393b9` | igor-lir | CC BY 4.0 | 31.7k / 1 | Realistic red-deer stag, one clip only |
| Wolf | Animated Wolf `23a3a563d48049d5b9844ddc1b5b6e79` | igor-lir | CC BY 4.0 | 27.3k / 1 | Realistic grey wolf, one clip only |
| Red fox | Animated Fox 3D Model `7b7d4f07d47a444ab6c08b62adfd4aff` | AnimalMesh3D | CC BY 4.0 | 19.5k / 69 | Realistic, full clip set |
| Hare | Animated Rabbit `244017d76f804d6eaa0dd2c33bcff50f` | AnimalMesh3D | CC BY 4.0 | 8.2k / 36 | Brown, hare-like proportions |
| Moose, reindeer, eagle, sheep, pony | none passed | | | | Only stylized, NC or low-poly found; next: paid realistic packs or a commissioned set |

### 7.6 Asset library pass 2 (10-10 c): what replaces what
Delivered to `assets/incoming/<asset>/` (GLB + PNG textures + `NOTES.md` each; contact sheet `assets/incoming/CONTACT_SHEET.jpg`). Every GLB holds its LODs as sibling nodes `<name>_LOD0`, `_LOD1`, ...; import with Godot's own LOD generation **off** for foliage cards (it collapses cards into holes) and switch by visibility range.

| Need | Asset | How it was made | Why |
|---|---|---|---|
| Scots pine x3 | `scots_pine_a/b/c` | Poly Haven `pine_tree_01` (CC0, 4-7 M triangles of real needles) baked to game trees by `tools/assets/cardify_tree.py`: trunk + biggest branches kept, twiglets dropped, bark re-unwrapped and baked to 2K; needles become cards showing 16 renders of real twig islands (8 top views on near-flat cards, 8 side views on vertical radial cards) | Real Scots-pine crown (layered, flat-topped, bare orange-grey trunk) instead of floating leaf confetti |
| Norway spruce x3 | `norway_spruce_a/b/c` | PlantCatalog "Realistic HD Norway spruce" 3/43, 13/43, 8/43 (CC BY 4.0) through the same card bake | Conical skirt to the ground; the Poly Haven fir has a bare pine-like trunk (kept as `fir_conifer_*` for mixed stands) |
| Birch x3 | `downy_birch_a/b/c` | lolipop_1707 "Five Birch trees pack" (CC BY 4.0), author's 4K maps reduced to 2K, our LOD3 (about 1.2k) | Real white birch with black lenticels; c is multi-stemmed like mountain birch. Silver-birch leaves, not true downy birch (no realistic downy birch found) |
| Tree impostors | `<species>_impostor_*` | `tools/assets/bake_impostors.py`, same 8 x 2 frame layout as `shaders/tree.gdshader` | Normals now rendered with the Raw view transform (the spike baker's Standard transform sRGB-encoded them) and alpha thickened x1.6 so far trees stay solid |
| Cliff bands | `rocks/cliff_*` (8) | Poly Haven scans decimated to 8k / 2.4k / 0.6k, baked to 4K, albedo graded to fjord gneiss (saturation 0.35, mean sRGB luminance 0.33) | True cliff faces for slopes above about 70 deg instead of stretched heightfield |
| Talus, boulders | `rocks/cliff_jagged_a/b` (talus aprons), `boulder_a`, `boulders_a` (cobbles), `stones_a` (pebbles) | Same bake, sets split into single stones sharing one 2K atlas; the two moss-stone sets were rejected (black patches from the source scans) | Cliff feet and shore |
| Cliff material | `cliff_materials/gneiss_banded`, `gneiss_dark`, `granite_lichen` | ambientCG Rock030 / Rock028 / Rock048 at 4K (albedo, normal GL, ORM, height) | Grey foliated rock with no wood-grain swirl; `gneiss_dark` and `granite_lichen` repeat visibly at 3 x 3, so break them with a macro noise or random rotation |
| Player | `player_luca` (Luca; alt `player_mike`) | Renderpeople scan (CC BY 4.0) + UAL clips by `tools/assets/retarget_char.py` | Scanned face holds at talk distance |
| Ingrid | `ingrid_farmer` | Sketchfab "Woman Farmer" (CC BY 4.0), welded, decimated 142k to 60k, albedo re-baked at 4K | Realistic woman in work clothes |
| Meadow | `ground_cover/meadow_*` | 16 Poly Haven plant renders, 10 side tiles for crossed-card clumps, 6 oblique tiles for far cover | Fills the flat meadow beyond 35 m |
| Village | `village_props/*` | 3 Sketchfab boats and 2 woodpiles (CC BY 4.0, 2K re-packed); skigard and hjell built by `tools/assets/build_skigard_hjell.py` | Village stops looking empty |

**Four questions, answered for pass 2**
- *Card trees near, impostors far:* 1) yes, trees fill every slope; 2) LOD0 13-18k triangles, two surfaces (bark opaque, leaves alpha-scissor), so keep LOD0 inside about 40 m, LOD1 (2-4k) to about 150 m, impostors beyond; alpha-tested overdraw is the real cost, so never alpha blend the leaves; 3) the cheaper trick is already the impostor; 4) fits.
- *Rock meshes on cliff bands:* 1) yes, walls are half the fjord frame; 2) 8k LOD0 opaque, one material, instance-friendly; LOD2 0.6k from about 250 m; 3) beyond about 1.5 km the terrain shader alone is cheaper and enough; 4) fits.
- *Scanned characters:* 1) the player is on screen 100 % of the time; 2) 21.5k triangles (Luca) and 60k (Ingrid) skinned, one material each: fine for 1-3 skinned meshes on screen; 3) none cheaper that still reads as a person at talk distance; 4) fits.
- *Ground clumps beyond 35 m:* 1) yes, the meadow is the foreground of most frames; 2) 6 triangles per clump, alpha-scissor, so density costs overdraw: cap at about 1 clump per 2 m2 from 35 to 120 m; 3) far tiles as flat cards past 80 m are the cheaper trick; 4) fits.

**Do / don't for these assets**
- Do keep the leaf and needle materials alpha-scissor (cutoff 0.4-0.5) with mipmapped alpha-to-coverage when MSAA is on; never alpha-blend foliage.
- Do multiply the leaf albedo by `COLOR_0` (crown AO, darker inside and low) and use `UV2.x` (0 trunk, 1 crown edge) as the wind-sway weight.
- Do rotate and scale instances (yaw random, scale 0.8-1.25; spruce from PlantCatalog 1.6-2.2 to reach 15-20 m).
- Don't tint the rock meshes beige; their albedo is already graded to gneiss. Don't recolour the birch bark.

## 8. Do and don't

**Do**
- Keep the world visible behind every screen; the place is the reward.
- Show the sim reason next to every price, every NPC mood and every closed path.
- Keep amber for wonder, teal for trade/yes, clay for missing/against you.
- Put the primary action bottom right, at least 130 px.
- Light the scene first, then fix materials, then grade.
- Look at every capture at phone size before calling it done.

**Don't**
- No purple, no blue-purple gradients, no glassmorphism, no glowing orbs in UI.
- No text under 32 px, no text panels under 0.80 alpha.
- No dusk sky with a high sun; no fog above 0.3 within 2 km outside the delta (far aerial perspective: rule 7.2.8).
- No golden-hour sun colour on a 30 deg sun.
- No quest markers floating over wonders (GDD P3: found by curiosity). Compass hints only after a rumor.
- No damage numbers, red flashes or "danger" styling: there is no combat.
- No stretched heightfield cliffs; use scan meshes on true cliff bands.
- No mock-ups in the store listing (studio rule): screenshots come from the real game.

## 9. Store assets

- **Icon (512 x 512, alpha, max 1 MB):** a single figure with a backpack on a rock shelf, small against a fjord wall in clear daylight, from the approved terrain; no text. Must still read at 48 px: test the silhouette, and if it fails, crop tighter to figure + one ridge line.
- **Feature graphic (1024 x 500, no alpha):** the fjord key frame, wide, village on the shore at right third, sky clear; game name in Source Serif 4 bold on the left sky. No "Best/#1/Free". Not plain white, black or dark grey.
- **Screenshots (from the real game via game-qa's capture bot):** 1) Skarvik Fjord from the village bench, 2) the market Sell tab during the river flood, 3) Ingrid talking (Trusted, flood line), 4) the Singing Cavern vista + card, 5) a house frame going up in build mode.

## 10. Visual tier: premium 3D, realistic variant

Hero scene first: **Skarvik Fjord village bench at 10:00, day light set** (`key_fjord_real_terrain.jpg` is the approved direction, owner 10-10). The owner signs it off from phone captures before any more level content.

### 10.1 Phone budget (my call, unmeasured: phone speed is only known from the PerfOverlay autoload on a real device)
| Item | High-end (60 fps) | Floor (30 fps) |
|---|---|---|
| Draw calls | at most 250 | at most 150 |
| Visible triangles | at most 400k | at most 200k |
| Shadowed lights | 1 directional, 2 cascades, 80 m | 1 directional, 1 cascade, 40 m |
| Terrain | one clipmap/LOD terrain, 2 detail layers + macro colour | same, 1 detail layer |
| Vegetation | MultiMesh, 3 LODs, impostors past 150 m, fade at 400 m | impostors past 80 m |
| NPCs | 12 full (T0, GDD 5.5) | 6 full |
| Textures | 2048 max, ASTC 6x6, total GPU memory under 1.2 GB | 1024 for props |
| Transparency | water, a few mist cards, glass; no full-screen transparent layers | |
| Post | tonemap + one LUT grade; no SSR, SSAO, SSIL, volumetric fog, DOF, motion blur | same |
| UI | no blur-behind on panels during gameplay; static blur of a captured frame is fine on paused screens | |

The look-dev renders use Blender Eevee with screen-space ray tracing; the phone must fake those effects: a baked reflection probe per bay plus a fresnel water shader (`game-studio/templates/shaders/stylized_water.gdshader` techniques with a realistic palette), baked lightmaps on the village, and height fog instead of volumetrics.

### 10.2 Four questions before any visual feature
1. Will the player notice it at the real camera distance (third person, about 4 m behind, 1.6 m up)?
2. What does it cost on the phone GPU (draw calls, overdraw, shader cost)?
3. Can a cheaper trick (baked light, texture, vertex colour, impostor, fake shadow) get the same look?
4. Does it fit this spec?
Spend on the sun and sky, near-camera materials (path, rocks, the village), characters' faces and hands, and water near the shore. Cut far detail, hidden interiors and tiny props.

Example (answered for shore foam on the fjord water): 1) yes, the shore is in the foreground of most village shots; 2) depth-intersection foam needs a depth-buffer copy per frame on the Mobile renderer; 3) a baked foam mask along the shore table from `dem_to_game.py` gives the same at the fixed coastline; 4) fits. Verdict: baked mask, not depth foam.

## 11. Credits obligations

CREDITS.md does not exist yet; create it with the first build. Required lines:

| Source | Licence | Obligation |
|---|---|---|
| Kartverket DTM 10 (Naeroyfjord terrain) | CC BY 4.0 (geonorge dddbb667-1303-4ac5-8640-7ec04c0e3918) | **Required**: "Terrain data © Kartverket" in the in-game credits **and** the store listing, link to kartverket.no where possible. Details: `assets/_raw/dem/SOURCE.md` |
| Inter | SIL OFL 1.1 | Ship `Inter-OFL.txt` with the game; list in credits |
| Source Serif 4 | SIL OFL 1.1 | Ship `SourceSerif4-OFL.txt`; list in credits |
| Poly Haven models, textures, HDRIs | CC0 | No obligation; credit "Poly Haven" as courtesy |
| Blender Studio Human Base Meshes | CC0 | No obligation; courtesy credit |
| MakeHuman system assets | CC0 | No obligation; courtesy credit |
| Copernicus GLO-30 (Kefalonia, Wadi Rum terrain) | Copernicus DEM licence (verified 10-10) | **Required** credit text, see `assets/_raw/dem/cop30/SOURCE.md` |
| Animal models (section 7.5) | CC BY 4.0 each | **Required**: author + model name + licence in the in-game credits for every model shipped |
| Sketchfab trees, boats, woodpiles, characters (section 7.6) | CC BY 4.0 each | **Required**: author + model name + licence in the in-game credits; exact lines in each `assets/incoming/<asset>/NOTES.md` |
| ambientCG materials | CC0 | No obligation; courtesy credit "ambientCG" |
| Quaternius Universal Animation Library | CC0 | No obligation; courtesy credit "Quaternius" |
| Voices (TTS model, future) | **open** (GDD 13) | Piper lessac/ryan are non-commercial and excluded; record the chosen model's licence here |

No personal names, internal paths or tool names in the in-game credits or the store text.
