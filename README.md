# Loki's Point-and-Click

[Click here to view my other scripts](https://github.com/Lorekeeper49/Loki-s-Ren-Py-scripts)

## INFORMATION

This is a proper working Point-and-Click system that you can use for certain sections of your Ren'Py game, or you could use it for the entire game too if you want.

Locations are written with a custom `location` statement instead of hand-built screens. Each location gets clickable hotspots, keyboard shortcuts with a shortcut bar along the bottom of the screen, and an optional minimap that opens when you hover the MAP button in the bottom-right corner. Movement and interactions can be locked behind conditions (like having an item) or behind a keypad code.

Requires Ren'Py 8.  ~~Unless you want to do a bunch of editing to remove all the Python3 syntax and other stuff that versions under Ren'py 8 doesn't support.~~

If you have any issues or suggestions for what should be added to these scripts and assets or the information area, list them in the issues tab

## Copyright policy

All of my scripts and assets are operated under the same copyright policy: you may use, edit, and redistribute these scripts and assets as you please, the only thing I ask for is that you credit me by name, "Lorekeeper49".  If you don't follow this policy, you can and will get flagged for stealing, so please cooperate and give me some credit for my hard work in making something useful for your games.

## FILES

- `01explore_statements.rpy`: defines the `location` statement. **Keep the `01` prefix.** Ren'Py reads files in filename order, and this file has to be read before any file that uses `location`, or Ren'Py will mistake your locations for dialogue lines.
- `explore.rpy`: the exploration loop, the screens, the keypad, and the settings you can change.
- `explore_demo.rpy` (optional): a small test house that shows off every feature. Start it with `call demo_explore`. It uses placeholder art, so it runs without any images. Delete it once you don't need it.

## HOW TO USE

### Quick start

```renpy
location "kitchen":
    minimap "map_house" zoom 0.5
    map_loc (420, 280)

    movement location "hallway" shortcut "w" map_loc (420, 120) xcenter 640 ycenter 120 xysize (300, 120) text "Hallway"
    interactable label "fridge_scene" shortcut "e" xcenter 300 ycenter 400 xysize (150, 250) text "Fridge"

label fridge_scene:
    "Nothing in here but expired milk."
    return

label start:
    call explore("kitchen", transition=dissolve)
    if _return:
        jump expression _return
```

- Call the `explore` label with the name of your first location. `transition` is used for the first location, and `return_label` is what `explore` returns if the section ends without naming a label.
- Labels called from an interactable must end with `return`. That brings the player back to the same location.

### Writing a location

```
location "name" [background <image>]:
    background <image>
    minimap <image> [transform properties]
    map_loc (x, y)

    show <image name> [at <transform>, ...] [as <tag>] [zorder <n>]
    add <displayable> [transform properties]

    movement [location] <target> [properties]
    interactable [action|label|item] <value> [properties]

    if <condition>:
        ...
    elif <condition>:
        ...
    else:
        ...
```

- **background**: the image behind the location. It can go on the `location` line or on its own line inside the block. If neither is given, the image `bg <name>` is used, so `location "kitchen"` shows `bg kitchen`.
- **minimap**: the image shown when the player hovers the MAP button. Transform properties like `zoom` can follow it.
- **map_loc**: where the "you are here" marker goes on the minimap.
- **show**: shows an image or sprite over the background, the same way Ren'Py's `show` statement does. Transform properties go in an indented block after a `:`.
- **add**: adds any displayable over the background, with transform properties on the same line. Useful for `Solid`, `Movie`, or a variable.
- **movement**: a hotspot that takes the player to another location.
- **interactable**: a hotspot that does something in place:
  - `label "x"` calls a label, then returns the player to the same location.
  - `item "x"` puts `x` in the `inventory`. The hotspot disappears once the item has been collected.
  - `action ...` runs any Ren'Py action. If you give it a string instead, it's treated as a label when one with that name exists, and as an item otherwise.
- **if / elif / else**: wrap any of the lines above, nested as deep as you like. Conditions are normal Python and don't need parentheses.

`show` and `add` images are drawn in the order you write them, and they stay on screen while a called label plays.

### Hotspot properties

These can follow a `movement` or `interactable`:

- `shortcut "w"`: the key that triggers the hotspot. It also shows up in the shortcut bar.
- `display_shortcut False`: keeps the shortcut working but hides it from the shortcut bar.
- `prerequisites <condition>`: the hotspot can't be clicked until the condition is true. Use `code("1234")` instead of a condition for a keypad lock (see below).
- `map_loc (x, y)`: movement only. Puts a button for this movement on the minimap.
- `transition <transition>`: for a movement, the transition into the next location. For an interactable label, the transition into the label.
- `text "Label"`: text in the middle of the hotspot. It's also the name shown in the shortcut bar and on the minimap.

Anything else is passed straight to the hotspot's button, so you position and style it with normal screen language properties: `xcenter`, `ycenter`, `xysize`, `background`, `hover_background`, and so on. You can write `hotspot_properties` before them to keep long lines readable; it's ignored.

Long lines can end with a `:` and continue in an indented block:

```renpy
    movement location "cellar" shortcut "c" prerequisites ("brass key" in inventory) map_loc (420, 440):
        xcenter 640 ycenter 600
        xysize (200, 100)
        text "Cellar"
```

Property values must be simple expressions, so wrap anything with operators in parentheses: `prerequisites ("key" in inventory)`, not `prerequisites "key" in inventory`.

### Keypad codes

```renpy
    movement location "study" prerequisites code("0451", name="study_door") xcenter 160 ycenter 360 xysize (200, 300)
```

Until the right code is entered, clicking the hotspot (or pressing its shortcut) opens the keypad. Once it's entered, the lock stays open for the rest of the game. A wrong code clears the input and shows "INCORRECT". The player can type on the keyboard or numpad, press Backspace to clear, Enter to submit, and Escape or BACK to close the keypad.

Options for `code()`:

- `name`: what the lock is saved as. Give two hotspots the same name to share one lock. Always set this for locks in a released game, because without it the lock is saved by its position in the location, and reordering the location later would break unlocks in players' saves.
- `limit_input=True`: submits automatically once enough digits are typed.
- `show_length=False`: hides the "4-DIGIT CODE" hint.

### Ending a section

- From a hotspot, use the action `ExploreLeave("next_label")`.
- From inside a called label, use `$ explore_leave("next_label")` and then `return`.

Either way, `explore` returns `"next_label"` in `_return`, so the line that called it can `jump expression _return`. Without a label, `explore` returns its `return_label`.

Don't `jump` out of a label called from a hotspot. It skips the cleanup at the end of the section.

### When things update

Hotspots, and the `if` blocks around them, update instantly. The background and the `show`/`add` images are redrawn when the player arrives at a location, after a called label returns, and after an item is picked up. If a plain Ren'Py action changes something those images depend on, add `ExploreRefresh()` to its action list:

```renpy
    interactable action [ToggleVariable("lamp_on"), ExploreRefresh()] text "Lamp" xcenter 1000 ycenter 300 xysize (100, 160)
```

### Variables

- `inventory`: everything the player has picked up. It's never reset, so check it for conditions anywhere in your game.
- `explored`: every location the player has visited. It's never reset either.
- `explore_unlocked`: the names of every keypad lock the player has opened.
- `explore_current` and `explore_previous`: the location the player is in and the one they came from.

### Settings

These are at the top of `explore.rpy`:

- `explore_default_transition`: the transition used for movement when none is given.
- `explore_hide_locked`: set to `True` to hide hotspots whose prerequisites aren't met, instead of showing them disabled.
- `explore_hide_collected`: set to `False` to keep item hotspots after the item is collected.
- `explore_bar_height`, `explore_map_toggle_size`, `explore_minimap_size`, `explore_map_pin_size`, `explore_map_here_size`, `explore_map_here_color`: sizes and colors for the shortcut bar and minimap.

Minimap positions are measured on the minimap image at its original size. If you `zoom` the minimap, the positions are scaled for you.

### Things to watch out for

- Shortcut keys can clash with Ren'Py's own keys. Avoid `h`, `s`, `f`, the arrow keys, Space, Enter and Tab unless you remove them from `config.keymap`.
- Two locations can't have the same name. Ren'Py will stop with an error if they do.
- Lint (in the launcher) checks that every movement goes to a real location and every interactable label exists.
