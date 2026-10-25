## explore_demo.rpy
##
## A small self-contained test house for the exploration system.
## Start it with:   call demo_explore
##
## Puzzle chain:
##   Library desk  -> torn note (tells you the study code 0451)
##   Hallway closet -> flashlight
##   Study (keypad 0451) -> brass key
##   Cellar (needs brass key; dark until you have the flashlight) -> garden key
##   Garden gate (needs garden key) -> leaves exploration
##
## Everything uses placeholder images defined below, so it runs without art.
## Swap the `image` definitions for real backgrounds/sprites later.

################################################################################
## Placeholder art
################################################################################

init python:
    def _demo_room(color, label):
        return Fixed(
            Solid(color),
            Text(label, size=72, color="#ffffff22", align=(0.5, 0.35)),
            )

    def _demo_map_room(x, y, w=160, h=100, color="#3a3a50"):
        return Transform(Solid(color), xysize=(w, h), pos=(x - w // 2, y - h // 2))

image bg demo_foyer = _demo_room("#2e2a3a", "FOYER")
image bg demo_hallway = _demo_room("#262633", "HALLWAY")
image bg demo_study = _demo_room("#33291f", "STUDY")
image bg demo_library = _demo_room("#1f2a24", "LIBRARY")
image bg demo_library_lit = _demo_room("#3f5a48", "LIBRARY")
image bg demo_cellar = _demo_room("#24201c", "CELLAR")
image bg demo_cellar_dark = _demo_room("#050505", "")
image bg demo_garden = _demo_room("#1c2b1c", "GARDEN")

image demo_ghost = Solid("#ffffff", xysize=(140, 360))

# Minimap is drawn at 800x600 and shown at zoom 0.5, to test map_loc scaling.
image demo_map = Fixed(
    Solid("#14141c"),
    _demo_map_room(400, 90, color="#2f4a2f"),     # garden
    _demo_map_room(180, 300),                     # study
    _demo_map_room(400, 300),                     # hallway
    _demo_map_room(620, 300),                     # library
    _demo_map_room(400, 480),                     # foyer
    _demo_map_room(180, 480, color="#2a2420"),    # cellar
    xysize=(800, 600),
    )

################################################################################
## State
################################################################################

default demo_note_read = False
default demo_lamp_on = False

################################################################################
## Locations
################################################################################

location "demo_foyer" background "bg demo_foyer":
    minimap "demo_map" zoom 0.5
    map_loc (400, 480)

    movement location "demo_hallway" shortcut "w" map_loc (400, 300) text "Hallway":
        xcenter 640 ycenter 120
        xysize (320, 120)

    # Boolean prerequisite: disabled until the brass key is in the inventory.
    movement location "demo_cellar" shortcut "x" prerequisites ("brass key" in inventory) map_loc (180, 480) text "Cellar":
        xcenter 200 ycenter 500
        xysize (200, 220)

    interactable label "demo_foyer_door" shortcut "e" text "Front door":
        xcenter 640 ycenter 560
        xysize (260, 180)


location "demo_hallway" background "bg demo_hallway":
    minimap "demo_map" zoom 0.5
    map_loc (400, 300)

    # Appears once you've read the note.
    if demo_note_read:
        show demo_ghost at right:
            alpha 0.12

    if "flashlight" not in inventory:
        add Solid("#d0d0d0", xysize=(70, 24)) xcenter 960 ycenter 470
        interactable item "flashlight" xcenter 960 ycenter 470 xysize (110, 70) text "?"

    # Keypad lock. The code is remembered once entered.
    movement location "demo_study" shortcut "q" prerequisites code("0451", name="study_door") map_loc (180, 300) text "Study":
        xcenter 160 ycenter 360
        xysize (200, 300)

    movement location "demo_library" shortcut "r" map_loc (620, 300) text "Library":
        xcenter 1120 ycenter 360
        xysize (200, 300)

    movement location "demo_foyer" shortcut "x" map_loc (400, 480) text "Foyer":
        xcenter 640 ycenter 640
        xysize (320, 80)

    movement location "demo_garden" shortcut "w" map_loc (400, 90) text "Back door":
        xcenter 640 ycenter 120
        xysize (240, 120)


location "demo_study" background "bg demo_study":
    minimap "demo_map" zoom 0.5
    map_loc (180, 300)

    if "brass key" not in inventory:
        add Solid("#c9a227", xysize=(36, 18)) xcenter 700 ycenter 430
        interactable item "brass key" shortcut "e" text "Desk drawer":
            xcenter 700 ycenter 430
            xysize (240, 120)
    else:
        interactable label "demo_study_empty" text "Desk drawer" display_shortcut False:
            xcenter 700 ycenter 430
            xysize (240, 120)

    movement location "demo_hallway" shortcut "r" map_loc (400, 300) text "Hallway":
        xcenter 1120 ycenter 360
        xysize (200, 300)


location "demo_library" background "bg demo_library":
    minimap "demo_map" zoom 0.5
    map_loc (620, 300)

    if demo_lamp_on:
        background "bg demo_library_lit"

    # A plain Ren'Py action. ExploreRefresh() redraws the background.
    interactable action [ToggleVariable("demo_lamp_on"), ExploreRefresh()] shortcut "t" text "Lamp":
        xcenter 1000 ycenter 300
        xysize (100, 160)

    # The desk is only searchable with the lamp on.
    interactable label "demo_library_desk" shortcut "e" prerequisites demo_lamp_on text "Desk":
        xcenter 560 ycenter 480
        xysize (300, 160)

    movement location "demo_hallway" shortcut "q" map_loc (400, 300) text "Hallway":
        xcenter 160 ycenter 360
        xysize (200, 300)


location "demo_cellar" background "bg demo_cellar_dark":
    minimap "demo_map" zoom 0.5
    map_loc (180, 480)

    if "flashlight" in inventory:
        background "bg demo_cellar"

        if "garden key" not in inventory:
            add Solid("#7fbf7f", xysize=(36, 18)) xcenter 900 ycenter 540
            interactable item "garden key" shortcut "e" text "Something shiny":
                xcenter 900 ycenter 540
                xysize (220, 100)

        interactable label "demo_cellar_crates" text "Crates":
            xcenter 360 ycenter 420
            xysize (260, 220)

    else:
        interactable label "demo_cellar_dark" shortcut "e" text "Feel around":
            xcenter 640 ycenter 400
            xysize (400, 300)

    movement location "demo_foyer" shortcut "w" map_loc (400, 480) text "Stairs up":
        xcenter 640 ycenter 120
        xysize (300, 120)


location "demo_garden" background "bg demo_garden":
    minimap "demo_map" zoom 0.5
    map_loc (400, 90)

    # Ends exploration once you have the key; disabled otherwise.
    interactable action ExploreLeave("demo_escaped") shortcut "e" prerequisites ("garden key" in inventory) text "Gate":
        xcenter 640 ycenter 200
        xysize (280, 200)

    interactable label "demo_garden_gate_locked" display_shortcut False:
        xcenter 640 ycenter 420
        xysize (280, 120)
        text "Rattle the gate"

    movement location "demo_hallway" shortcut "x" map_loc (400, 300) text "Back inside":
        xcenter 640 ycenter 640
        xysize (320, 80)

################################################################################
## Labels
################################################################################

label demo_explore:
    $ inventory = []
    $ explored = []
    $ explore_unlocked = set()
    $ demo_note_read = False
    $ demo_lamp_on = False

    call explore("demo_foyer", transition=dissolve)

    if _return:
        jump expression _return

    return

label demo_foyer_door:
    "The front door won't budge. Something is holding it shut from the outside."
    return

label demo_study_empty:
    "The drawer is empty now."
    return

label demo_library_desk:
    if not demo_note_read:
        "Under a stack of papers there's a torn note."
        "Four digits are scrawled across it: 0451."
        $ demo_note_read = True
        $ inventory.append("torn note")
    else:
        "Just papers. You already took the note."
    return

label demo_cellar_dark:
    "It's pitch black. Your hand brushes something cold and you pull back."
    "You need a light."
    return

label demo_cellar_crates:
    "Old crates, mostly empty. One is full of jars with the labels scratched off."
    return

label demo_garden_gate_locked:
    if "garden key" in inventory:
        "The gate has a lock. Your garden key looks like it would fit."
    else:
        "The gate is padlocked."
    return

label demo_escaped:
    scene black with dissolve
    "The gate swings open, and you step out into the night."
    $ demo_items = ", ".join(inventory)
    "You made it out with: [demo_items]."
    return
