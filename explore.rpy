init -501 style explore_button:
    background "#6464646c"
    hover_background "#ffffff6c"

init -501 style explore_text:
    font "mod_assets/fonts/FOT-RodinNTLG Pro EB.otf"
    size 25
    color "#ffffff6c"
    text_align 0.5

init -501 style explore_button_text:
    font "mod_assets/fonts/FOT-RodinNTLG Pro EB.otf"
    size 25
    color "#ffffff6c"
    text_align 0.5

init -1 python:
    """
    for all screens: style_prefix "explore"
    button template 1 (worse option):
        button xcenter x ycenter y xysize (width, height) action ButtonAction(next_location, dialogue, or save_var)
        text "label" xcenter x ycenter y
    button template 2 (better option):
        button:
            xcenter x
            ycenter y
            xysize (width, height)
            action ButtonAction(next_location, dialogue, or save_var)
            text "label" align (0.5, 0.5)
    """

label explore(start, *args, transition=None, return_label=None, **kwargs):
    scene expression "bg [start]"
    show screen quick_menu
    with transition
    $ codes = []
    $ explored = []
    $ renpy.call_screen(start, args, kwargs)
    hide screen quick_menu
    return return_label

default jumpnum = 0
label next_location(loc, *args, transition=Fade(0.25, 0.0, 0.25), **kwargs):
    scene expression "bg [loc]"
    with transition
    $ renpy.call_screen(loc, args, kwargs)
    return

default inventory = []
default explored = []
default party = []
default code = ""
default dial = ""
default prev_loc = ""
default to_input = ""
default codes = []

label dialpad(c, p, s, limit_input=False, show_code_length=True):
    $ code = c
    $ prev_loc = p
    $ dial = ""
    $ to_input = s
    call screen code_input(limit_input, show_code_length)
    return

screen code_input(limit_input=False, show_code_length=True):
    style_prefix "explore"
    add "vignette"
    text "[dial]" xcenter 640 ycenter 140
    button xcenter 750 ycenter 580 xysize (100, 100) action [If(dial == code, AddToSet(codes, to_input)), Call("next_location", prev_loc, transition=False)]
    text "入力\nENTER" xcenter 750 ycenter 580
    button xcenter 530 ycenter 580 xysize (100, 100) action SetVariable("dial", "")
    text "クリア\nCLEAR" xcenter 530 ycenter 580
    button xcenter 640 ycenter 580 xysize (100, 100) action [SetVariable("dial", dial + "0"), If(limit_input, If(len(dial) >= len(code), [If(dial == code, AddToSet(codes, to_input)), Call("next_location", prev_loc, transition=False)]))]
    text "0" xcenter 640 ycenter 580
    button xcenter 530 ycenter 470 xysize (100, 100) action [SetVariable("dial", dial + "1"), If(limit_input, If(len(dial) >= len(code), [If(dial == code, AddToSet(codes, to_input)), Call("next_location", prev_loc, transition=False)]))]
    text "1" xcenter 530 ycenter 470
    button xcenter 640 ycenter 470 xysize (100, 100) action [SetVariable("dial", dial + "2"), If(limit_input, If(len(dial) >= len(code), [If(dial == code, AddToSet(codes, to_input)), Call("next_location", prev_loc, transition=False)]))]
    text "2" xcenter 640 ycenter 470
    button xcenter 750 ycenter 470 xysize (100, 100) action [SetVariable("dial", dial + "3"), If(limit_input, If(len(dial) >= len(code), [If(dial == code, AddToSet(codes, to_input)), Call("next_location", prev_loc, transition=False)]))]
    text "3" xcenter 750 ycenter 470
    button xcenter 530 ycenter 360 xysize (100, 100) action [SetVariable("dial", dial + "4"), If(limit_input, If(len(dial) >= len(code), [If(dial == code, AddToSet(codes, to_input)), Call("next_location", prev_loc, transition=False)]))]
    text "4" xcenter 530 ycenter 360
    button xcenter 640 ycenter 360 xysize (100, 100) action [SetVariable("dial", dial + "5"), If(limit_input, If(len(dial) >= len(code), [If(dial == code, AddToSet(codes, to_input)), Call("next_location", prev_loc, transition=False)]))]
    text "5" xcenter 640 ycenter 360
    button xcenter 750 ycenter 360 xysize (100, 100) action [SetVariable("dial", dial + "6"), If(limit_input, If(len(dial) >= len(code), [If(dial == code, AddToSet(codes, to_input)), Call("next_location", prev_loc, transition=False)]))]
    text "6" xcenter 750 ycenter 360
    button xcenter 530 ycenter 250 xysize (100, 100) action [SetVariable("dial", dial + "7"), If(limit_input, If(len(dial) >= len(code), [If(dial == code, AddToSet(codes, to_input)), Call("next_location", prev_loc, transition=False)]))]
    text "7" xcenter 530 ycenter 250
    button xcenter 640 ycenter 250 xysize (100, 100) action [SetVariable("dial", dial + "8"), If(limit_input, If(len(dial) >= len(code), [If(dial == code, AddToSet(codes, to_input)), Call("next_location", prev_loc, transition=False)]))]
    text "8" xcenter 640 ycenter 250
    button xcenter 750 ycenter 250 xysize (100, 100) action [SetVariable("dial", dial + "9"), If(limit_input, If(len(dial) >= len(code), [If(dial == code, AddToSet(codes, to_input)), Call("next_location", prev_loc, transition=False)]))]
    text "9" xcenter 750 ycenter 250
    if show_code_length:
        text "[len(code)]-DIGIT CODE" xcenter 640 ycenter 40