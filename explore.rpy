## explore.rpy
##
## Runtime half of the exploration system: the explore loop, the location
## screen (hotspots, shortcut bar, hover minimap) and the keypad.
## The `location` statement itself lives in explore_statements.rpy.
## Targets current Ren'Py 8.
##
## Example
## -------
##
## location "kitchen" background "bg kitchen":
##     minimap "map_house" zoom 0.5
##     map_loc (420, 280)
##
##     show sayori neutral at right
##     add "kitchen_steam" xpos 300 ypos 180 alpha 0.6
##
##     if "flashlight" not in inventory:
##         show flashlight_prop:
##             xpos 900 ypos 450
##         interactable item "flashlight" xcenter 900 ycenter 450 xysize (80, 80)
##
##     if lights_on:
##         background "bg kitchen_lit"
##     else:
##         add Solid("#00000088")
##
##     movement location "hallway" shortcut "w" map_loc (420, 120) xcenter 640 ycenter 120 xysize (300, 120) text "Hallway"
##
##     movement location "cellar" shortcut "c" prerequisites code("0451") map_loc (420, 440) transition dissolve:
##         xcenter 640 ycenter 600
##         xysize (200, 100)
##         text "Cellar"
##
##     interactable action "fridge_scene" shortcut "e" xcenter 300 ycenter 400 xysize (150, 250) text "Fridge"
##     interactable action [SetVariable("lights_on", True), ExploreRefresh()] xcenter 1100 ycenter 300 xysize (60, 100)
##
## label fridge_scene:
##     "Nothing in here but expired milk."
##     return                              # back to the kitchen
##
## label start:
##     call explore("kitchen", transition=dissolve)
##     if _return:
##         jump expression _return
##
## Interactable values:
##     label "x"   - called, then exploration resumes at the same location
##     item "x"    - added to `inventory`; hotspot disappears once collected
##     action ...  - a string is treated as a label if one exists, otherwise an
##                   item; anything else is run as a Ren'Py action
##
## When things redraw:
##     Hotspots (and the `if` blocks around them) update instantly.
##     The background, `show` and `add` images are drawn when you arrive, after
##     a called label returns, and after an item is picked up. If a plain
##     Ren'Py action changes something those images depend on, add
##     ExploreRefresh() to its action list.
##
## To end exploration from inside an interactable label, use
## `$ explore_leave("next_label")` (or `explore_leave()`) and then `return`.
## From a hotspot, use the action ExploreLeave("next_label").
## `call explore(...)` returns that label name (or return_label) in _return.

################################################################################
## Configuration
################################################################################

define explore_default_transition = Fade(0.25, 0.0, 0.25)

# Hide hotspots whose prerequisites are False instead of showing them disabled.
define explore_hide_locked = False

# Hide item hotspots once the item is in the inventory.
define explore_hide_collected = True

define explore_bar_height = 48
define explore_map_toggle_size = (140, 48)
define explore_minimap_size = (400, 300)
define explore_map_pin_size = (24, 24)
define explore_map_here_size = (16, 16)
define explore_map_here_color = "#ff4040"

################################################################################
## Styles
################################################################################

init -501 style explore_button:
    background "#6464646c"
    hover_background "#ffffff6c"

init -501 style explore_text:
    size 25
    color "#ffffff6c"
    text_align 0.5

init -501 style explore_button_text:
    size 25
    color "#ffffff6c"
    text_align 0.5

init -501 style explore_hud_frame is frame:
    background "#000000aa"
    padding (20, 0)

init -501 style explore_hud_text is text:
    size 20
    color "#ffffffcc"
    yalign 0.5

init -501 style explore_map_toggle is button:
    background "#6464646c"
    hover_background "#ffffff6c"

init -501 style explore_map_toggle_text is text:
    size 22
    color "#ffffffcc"

init -501 style explore_map_panel is frame:
    background "#000000cc"
    padding (0, 0)

init -501 style explore_map_pin is button:
    background "#ffffffaa"
    hover_background "#ffd700"
    insensitive_background "#55555588"

init -501 style explore_map_tip is text:
    size 18
    color "#ffffff"
    outlines [ (2, "#000000", 0, 0) ]

################################################################################
## State
################################################################################

default inventory = []
default explored = []
default party = []

default explore_current = None
default explore_previous = None
default explore_unlocked = set()

default _explore_leave = None
default _explore_next_trans = None
default _explore_call_trans = None
default _explore_dial = ""
default _explore_dial_msg = ""

################################################################################
## Python
################################################################################

init -100 python:

    # Runtime-only bookkeeping (never assigned to, so never saved).
    _explore_runtime = {"predicting": ()}

    class ExploreCode:
        """
        Use as `prerequisites code("1234")`. Until the code is entered, the
        hotspot opens the keypad; afterwards it works normally.

        `name` identifies the lock in explore_unlocked. By default it's
        "<location>:<node id>", so give it a name if two hotspots should
        share one lock, or if you expect to reorder a location after release.
        """

        def __init__(self, digits, name=None, limit_input=False, show_length=True):
            self.digits = str(digits)
            self.name = name
            self.limit_input = limit_input
            self.show_length = show_length

    code = ExploreCode

    def _explore_ev(expr, default=None):
        # py_eval caches compiled expressions, so this is cheap per frame.
        if expr is None:
            return default
        return renpy.python.py_eval(expr)

    def _explore_eval_props(node):
        return {k: _explore_ev(v) for k, v in node["props"].items()}

    def _explore_node(loc, node_id):
        return _explore_registry[loc]["by_id"][node_id]

    def explore_leave(label=None):
        store._explore_leave = label if label is not None else True

    def ExploreLeave(label=None):
        return Return(("leave", label))

    def ExploreRefresh():
        return Return(("refresh",))

    ############################################################################
    ## Resolving a location's if-blocks.

    def _explore_resolve_nodes(nodes, res):
        for n in nodes:
            t = n["type"]

            if t == "if":
                for cond, children in n["branches"]:
                    if cond is None or _explore_ev(cond):
                        _explore_resolve_nodes(children, res)
                        break

            elif t == "background":
                res["background"] = n["value"]
            elif t == "minimap":
                res["minimap"] = n
            elif t == "map_loc":
                res["map_loc"] = n["value"]
            elif t in ("show", "add"):
                res["images"].append(n)
            else:
                res["entries"].append(n)

    def _explore_resolve(loc):
        """
        Returns the nodes of a location that are active right now.
        """

        data = _explore_registry[loc]
        res = {
            "background": data["background"],
            "minimap": None,
            "map_loc": None,
            "entries": [],
            "images": [],
            }

        _explore_resolve_nodes(data["nodes"], res)
        return res

    def _explore_background(loc, res=None):
        if loc not in _explore_registry:
            return f"bg {loc}"
        if res is None:
            res = _explore_resolve(loc)
        return _explore_ev(res["background"], f"bg {loc}")

    ############################################################################
    ## Drawing the scene.

    def _explore_draw(loc):
        if loc not in store.explored:
            store.explored.append(loc)

        renpy.scene()

        if loc not in _explore_registry:
            renpy.show(f"bg {loc}")
            return

        res = _explore_resolve(loc)

        bg = _explore_background(loc, res)
        if isinstance(bg, str):
            renpy.show(bg)
        else:
            renpy.show("explore_bg", what=bg)

        for n in res["images"]:
            props = _explore_eval_props(n)

            if n["type"] == "show":
                at_list = [_explore_ev(a) for a in n["at"]]
                if props:
                    at_list.append(Transform(**props))

                renpy.show(n["name"], at_list=at_list, tag=n["tag"], zorder=_explore_ev(n["zorder"], 0))

            else:
                d = _explore_ev(n["value"])
                if props:
                    d = Transform(d, **props)

                renpy.show(f"explore_add_{n['id']}", what=d)

        _explore_predict_neighbors(res)

    def _explore_stop_predict():
        for d in _explore_runtime["predicting"]:
            renpy.stop_predict(d)
        _explore_runtime["predicting"] = ()

    def _explore_predict_neighbors(res):
        """
        Starts loading the backgrounds of every location reachable from here.
        """

        bgs = []

        for n in res["entries"]:
            if n["type"] != "movement":
                continue
            try:
                bgs.append(_explore_background(_explore_ev(n["value"])))
            except Exception:
                pass

        _explore_stop_predict()

        for d in bgs:
            try:
                renpy.start_predict(d)
            except Exception:
                pass

        _explore_runtime["predicting"] = tuple(bgs)

    ############################################################################
    ## Hotspots.

    def _explore_resolve_mode(mode, value):
        if mode != "auto":
            return mode
        if isinstance(value, str):
            return "label" if renpy.has_label(value) else "item"
        return "action"

    class _ExploreHotspot(python_object):
        __slots__ = ("kind", "text", "label", "props", "shortcut", "show_shortcut",
                     "map_loc", "action", "sensitive")

    def _explore_hotspots(loc, res):
        """
        Evaluates the active entries of a location for the current frame.
        """

        rv = []

        for n in res["entries"]:

            h = _ExploreHotspot()
            h.kind = n["type"]
            h.text = _explore_ev(n.get("text"))
            h.props = _explore_eval_props(n)
            h.shortcut = _explore_ev(n.get("shortcut"))
            h.show_shortcut = _explore_ev(n.get("display_shortcut"), True)
            h.map_loc = _explore_ev(n.get("map_loc"))

            value = _explore_ev(n["value"])

            if n["type"] == "movement":
                action = Return(("move", loc, n["id"]))

            else:
                match _explore_resolve_mode(n["mode"], value):
                    case "label":
                        action = Return(("call", loc, n["id"]))
                    case "item":
                        if explore_hide_collected and value in store.inventory:
                            continue
                        action = Return(("item", loc, n["id"]))
                    case _:
                        action = value

            if h.text is not None:
                h.label = str(h.text)
            elif isinstance(value, str):
                h.label = value
            else:
                h.label = ""

            sensitive = True
            pre = n.get("prerequisites")

            if pre is not None:
                req = _explore_ev(pre)

                if isinstance(req, ExploreCode):
                    lock_id = req.name or f"{loc}:{n['id']}"

                    if lock_id not in store.explore_unlocked:
                        action = Show("explore_dialpad", lock=req, lock_id=lock_id, success=action)

                else:
                    sensitive = bool(req)

            if not sensitive and explore_hide_locked:
                continue

            h.action = action
            h.sensitive = sensitive
            rv.append(h)

        return rv

    def _explore_minimap(node, map_loc):
        """
        Returns (displayable, xzoom, yzoom, here) for a minimap node.
        map_loc coordinates are in the unzoomed image's space and get scaled
        by any zoom/xzoom/yzoom given on the minimap line.
        """

        props = _explore_eval_props(node)

        zoom = props.get("zoom", 1.0)
        zx = zoom * props.get("xzoom", 1.0)
        zy = zoom * props.get("yzoom", 1.0)

        disp = Transform(_explore_ev(node["value"]), **props)

        here = _explore_ev(map_loc)
        if here is not None:
            here = (int(here[0] * zx), int(here[1] * zy))

        return disp, zx, zy, here

    def _explore_key_name(k):
        name = k
        mods = []

        while True:
            for m in ("repeat_", "keydown_", "keyup_", "noshift_", "shift_", "ctrl_", "alt_", "meta_"):
                if name.startswith(m):
                    name = name[len(m):]
                    if m in ("shift_", "ctrl_", "alt_", "meta_"):
                        mods.append(m[:-1].upper())
                    break
            else:
                break

        name = name.removeprefix("K_")
        return "+".join(mods + [name.upper()])

    def _explore_bar_label(h):
        return f"[{_explore_key_name(h.shortcut)}]  {h.label}"

    ############################################################################
    ## Results from the location screen.

    def _explore_handle(result):
        """
        Processes what the location screen returned. Returns a label to
        call, or None.
        """

        match result:

            case ("move", src, node_id):
                n = _explore_node(src, node_id)
                store.explore_previous = src
                store.explore_current = _explore_ev(n["value"])
                store._explore_next_trans = _explore_ev(n.get("transition"), explore_default_transition)

            case ("call", src, node_id):
                n = _explore_node(src, node_id)
                store._explore_call_trans = _explore_ev(n.get("transition"))
                return _explore_ev(n["value"])

            case ("item", src, node_id):
                value = _explore_ev(_explore_node(src, node_id)["value"])
                if value not in store.inventory:
                    store.inventory.append(value)

            case ("leave", label):
                explore_leave(label)

        return None

    ############################################################################
    ## Keypad.

    def _explore_dial_submit(lock, lock_id, success):

        if store._explore_dial == lock.digits:
            store.explore_unlocked.add(lock_id)
            store._explore_dial = ""
            store._explore_dial_msg = ""
            renpy.hide_screen("explore_dialpad")

            rv = renpy.run(success)
            renpy.restart_interaction()
            return rv

        store._explore_dial = ""
        store._explore_dial_msg = "INCORRECT"
        renpy.restart_interaction()

    class _ExploreDialPress(Action):
        identity_fields = ["lock", "success"]
        equality_fields = ["digit", "lock_id"]

        def __init__(self, digit, lock, lock_id, success):
            self.digit = digit
            self.lock = lock
            self.lock_id = lock_id
            self.success = success

        def __call__(self):
            store._explore_dial_msg = ""
            store._explore_dial += self.digit

            if self.lock.limit_input and len(store._explore_dial) >= len(self.lock.digits):
                return _explore_dial_submit(self.lock, self.lock_id, self.success)

            renpy.restart_interaction()

    class _ExploreDialSubmit(Action):
        identity_fields = ["lock", "success"]
        equality_fields = ["lock_id"]

        def __init__(self, lock, lock_id, success):
            self.lock = lock
            self.lock_id = lock_id
            self.success = success

        def __call__(self):
            return _explore_dial_submit(self.lock, self.lock_id, self.success)

################################################################################
## The explore loop
################################################################################

label explore(start, transition=None, return_label=None):
    $ explore_current = start
    $ explore_previous = None
    $ _explore_leave = None
    $ _explore_next_trans = transition

    show screen quick_menu

    while _explore_leave is None:

        $ _explore_draw(explore_current)
        $ renpy.with_statement(_explore_next_trans)
        $ _explore_next_trans = None

        if explore_current in _explore_registry:
            call screen explore_location(explore_current)
        else:
            # Fallback: a plain screen with the location's name.
            $ _return = renpy.call_screen(explore_current)

        $ _explore_call = _explore_handle(_return)

        if _explore_call is not None:
            $ renpy.with_statement(_explore_call_trans)
            $ _explore_call_trans = None
            call expression _explore_call

    hide screen quick_menu
    $ _explore_stop_predict()

    $ _explore_after = return_label if _explore_leave is True else _explore_leave
    $ _explore_leave = None

    return _explore_after

################################################################################
## Screens
################################################################################

screen explore_location(loc):
    style_prefix "explore"

    default map_open = False

    $ res = _explore_resolve(loc)
    $ hotspots = _explore_hotspots(loc, res)
    $ has_map = res["minimap"] is not None

    ## Hotspots and their shortcuts.
    for h in hotspots:
        button:
            properties h.props
            sensitive h.sensitive
            action h.action
            if h.text is not None:
                text h.text align (0.5, 0.5)

        if h.shortcut and h.sensitive:
            key h.shortcut action h.action

    ## Shortcut bar.
    frame:
        style "explore_hud_frame"
        xfill True
        ysize explore_bar_height
        yalign 1.0
        if has_map:
            right_padding explore_map_toggle_size[0] + 20

        hbox:
            spacing 40
            yalign 0.5

            for h in hotspots:
                if h.shortcut and h.show_shortcut and h.sensitive:
                    text _explore_bar_label(h) style "explore_hud_text" substitute False

    ## Minimap.
    if has_map:
        $ mw, mh = explore_minimap_size
        $ tw, th = explore_map_toggle_size
        $ sw, sh = config.screen_width, config.screen_height
        $ map_x, map_y = sw - mw, sh - explore_bar_height - mh

        # Opens on hovering the toggle; stays open while the mouse is over
        # the toggle or the map, closes when it leaves both.
        mousearea:
            if map_open:
                area (map_x, map_y, mw, mh + explore_bar_height)
            else:
                area (sw - tw, sh - th, tw, th)
            hovered If(not map_open, SetScreenVariable("map_open", True))
            unhovered If(map_open, SetScreenVariable("map_open", False))

        button:
            style "explore_map_toggle"
            xysize explore_map_toggle_size
            align (1.0, 1.0)
            action ToggleScreenVariable("map_open")
            text "MAP" style "explore_map_toggle_text" align (0.5, 0.5)

        if map_open:
            $ mdisp, zx, zy, here = _explore_minimap(res["minimap"], res["map_loc"])
            $ tip = GetTooltip()

            frame:
                style "explore_map_panel"
                pos (map_x, map_y)
                xysize (mw, mh)

                fixed:
                    add mdisp

                    if here is not None:
                        add Solid(explore_map_here_color) xysize explore_map_here_size pos here anchor (0.5, 0.5)

                    for h in hotspots:
                        if h.kind == "movement" and h.map_loc is not None:
                            button:
                                style "explore_map_pin"
                                pos (int(h.map_loc[0] * zx), int(h.map_loc[1] * zy))
                                anchor (0.5, 0.5)
                                xysize explore_map_pin_size
                                sensitive h.sensitive
                                action h.action
                                tooltip h.label

                    if tip:
                        text tip style "explore_map_tip" pos (10, 8) substitute False


screen explore_dialpad(lock, lock_id, success):
    modal True
    zorder 200
    style_prefix "explore"

    on "show" action [SetVariable("_explore_dial", ""), SetVariable("_explore_dial_msg", "")]

    if lock.show_length:
        text f"{len(lock.digits)}-DIGIT CODE" xcenter 640 ycenter 40

    text _explore_dial xcenter 640 ycenter 140 substitute False

    if _explore_dial_msg:
        text _explore_dial_msg xcenter 640 ycenter 190 substitute False

    for i, d in enumerate("789456123"):
        button:
            xcenter 530 + 110 * (i % 3)
            ycenter 250 + 110 * (i // 3)
            xysize (100, 100)
            action _ExploreDialPress(d, lock, lock_id, success)
            text d align (0.5, 0.5)

        key d action _ExploreDialPress(d, lock, lock_id, success)
        key f"K_KP{d}" action _ExploreDialPress(d, lock, lock_id, success)

    button:
        xcenter 530 ycenter 580 xysize (100, 100)
        action [SetVariable("_explore_dial", ""), SetVariable("_explore_dial_msg", "")]
        text "CLEAR" align (0.5, 0.5)

    button:
        xcenter 640 ycenter 580 xysize (100, 100)
        action _ExploreDialPress("0", lock, lock_id, success)
        text "0" align (0.5, 0.5)

    button:
        xcenter 750 ycenter 580 xysize (100, 100)
        action _ExploreDialSubmit(lock, lock_id, success)
        text "ENTER" align (0.5, 0.5)

    button:
        xcenter 640 ycenter 680 xysize (320, 60)
        action Hide("explore_dialpad")
        text "BACK" align (0.5, 0.5)

    key "0" action _ExploreDialPress("0", lock, lock_id, success)
    key "K_KP0" action _ExploreDialPress("0", lock, lock_id, success)
    key "K_BACKSPACE" action [SetVariable("_explore_dial", ""), SetVariable("_explore_dial_msg", "")]
    key "K_RETURN" action _ExploreDialSubmit(lock, lock_id, success)
    key "K_KP_ENTER" action _ExploreDialSubmit(lock, lock_id, success)
    key "game_menu" action Hide("explore_dialpad")
