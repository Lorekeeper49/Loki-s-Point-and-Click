## 01explore_statements.rpy
##
## Defines the `location` creator-defined statement used by the exploration
## system (see explore.rpy for the runtime half). Targets current Ren'Py 8.
##
## The "01" prefix matters: Ren'Py parses files in filename order, and this
## file has to be parsed before any file that uses `location`. If you move or
## rename it, keep it sorting first.
##
## Syntax
## ------
##
## location "name" [background <image>]:
##     background <image>              # alternative to the header property
##     minimap <image> [transform properties...]
##     map_loc (x, y)                  # "you are here" marker on the minimap
##
##     show <image name> [at <transform>, ...] [as <tag>] [zorder <n>] [:]
##         <transform properties>      # optional block, one or more per line
##     add <displayable expr> [transform properties...] [:]
##
##     movement [location] <target> [entry properties...] [hotspot properties...] [:]
##     interactable [action|label|item] <value> [entry properties...] [hotspot properties...] [:]
##
##     if <condition>:
##         <any of the lines above, including nested ifs>
##     elif <condition>:
##         ...
##     else:
##         ...
##
## Background defaults to the image "bg <name>". `show` and `add` images are
## drawn over it in the order they're written, and stay up during dialogue
## called from an interactable.
##
## Entry properties:
##     shortcut "w"                    keysym that triggers this entry
##     display_shortcut False          hide it from the shortcut bar (default True)
##     prerequisites <expr>            a condition, or code("1234") for a keypad lock
##     map_loc (x, y)                  movement only: pin position on the minimap
##     transition <expr>               movement: transition into the target
##                                     interactable label: transition into the label
##     text "Label"                    text centered in the hotspot (also used in the bar)
##
## Anything else on an entry is passed to the hotspot button as a screen
## language property (xcenter, ycenter, xysize, background, ...). The word
## `hotspot_properties` is accepted and ignored, as a visual separator.
##
## Any line can end with ':' and continue its properties in an indented block.
## Property values are simple expressions: wrap anything with operators in
## parentheses, e.g. prerequisites ("key" in inventory). `if` conditions are
## full Python expressions and don't need parentheses.

python early:

    _explore_registry = {}

    # Keywords that configure a node itself rather than its displayable.
    _EXPLORE_NODE_KEYWORDS = {
        "movement": {"shortcut", "display_shortcut", "prerequisites", "map_loc", "transition", "text"},
        "interactable": {"shortcut", "display_shortcut", "prerequisites", "transition", "text"},
        "minimap": set(),
        "show": set(),
        "add": set(),
    }

    # Nodes that get an id (used to look entries back up, and for image tags).
    _EXPLORE_INDEXED = {"movement", "interactable", "show", "add"}

    def _explore_parse_props(lx, node, stmt):
        """
        Parses `keyword value` pairs up to the end of the line. Returns True
        if the line ended with ':' (meaning a property block follows).
        """

        known = _EXPLORE_NODE_KEYWORDS[stmt]

        while not lx.eol():

            if lx.match(r':'):
                return True

            kw = lx.word()

            if kw is None:
                lx.error("expected a property name")

            if kw == "hotspot_properties":
                continue

            if kw == "prerequisite":
                kw = "prerequisites"

            if kw == "map_loc" and kw not in known:
                lx.error("map_loc is only allowed on a movement, or directly in a location")

            value = lx.require(lx.simple_expression)

            if kw in known:
                node[kw] = value
            else:
                node["props"][kw] = value

        return False

    def _explore_parse_prop_block(lx, node, stmt):
        lx.expect_eol()
        lx.expect_block(stmt)

        sub = lx.subblock_lexer()

        while sub.advance():
            if _explore_parse_props(sub, node, stmt):
                sub.error("nested blocks are not allowed here")
            sub.expect_noblock(f"{stmt} property")

    def _explore_parse_rest(lx, node, stmt):
        """
        Parses the rest of a node's line, plus its optional property block.
        """

        if _explore_parse_props(lx, node, stmt):
            _explore_parse_prop_block(lx, node, stmt)
        else:
            lx.expect_noblock(stmt)

    def _explore_parse_image_name(ll):
        # Same approach as Ren'Py's own show statement: image name components
        # stop at keywords like at/as/zorder.
        name = [ll.require(ll.image_name_component)]

        while (part := ll.image_name_component()):
            name.append(part)

        return tuple(name)

    def _explore_parse_show(ll):
        node = {
            "type": "show",
            "name": _explore_parse_image_name(ll),
            "at": [],
            "tag": None,
            "zorder": None,
            "props": {},
            }

        while True:

            if ll.eol():
                ll.expect_noblock("show")
                break

            if ll.match(r':'):
                _explore_parse_prop_block(ll, node, "show")
                break

            if ll.keyword("at"):
                node["at"].append(ll.require(ll.simple_expression))
                while ll.match(r','):
                    node["at"].append(ll.require(ll.simple_expression))

            elif ll.keyword("as"):
                node["tag"] = ll.require(ll.word)

            elif ll.keyword("zorder"):
                node["zorder"] = ll.require(ll.simple_expression)

            else:
                ll.error("expected at, as, zorder, or ':' (put transform properties in a block)")

        return node

    def _explore_parse_branch(ll, nodes, stmt, cond):
        """
        Attaches an elif/else branch to the if node just before it.
        """

        if not nodes or nodes[-1]["type"] != "if" or nodes[-1]["closed"]:
            ll.error(f"{stmt} without a matching if")

        if cond is None:
            nodes[-1]["closed"] = True

        ll.require(r':')
        ll.expect_eol()
        ll.expect_block(stmt)

        children = []
        _explore_parse_children(ll.subblock_lexer(), children)
        nodes[-1]["branches"].append((cond, children))

    def _explore_parse_children(ll, nodes):
        """
        Parses the lines of a location (or of an if/elif/else branch) into
        a list of nodes.
        """

        while ll.advance():

            if ll.keyword("if"):
                cond = ll.require(ll.python_expression)
                ll.require(r':')
                ll.expect_eol()
                ll.expect_block("if")

                children = []
                _explore_parse_children(ll.subblock_lexer(), children)
                nodes.append({"type": "if", "branches": [(cond, children)], "closed": False})

            elif ll.keyword("elif"):
                _explore_parse_branch(ll, nodes, "elif", ll.require(ll.python_expression))

            elif ll.keyword("else"):
                _explore_parse_branch(ll, nodes, "else", None)

            elif ll.keyword("background"):
                nodes.append({"type": "background", "value": ll.require(ll.simple_expression)})
                ll.expect_eol()
                ll.expect_noblock("background")

            elif ll.keyword("minimap"):
                node = {"type": "minimap", "value": ll.require(ll.simple_expression), "props": {}}
                _explore_parse_rest(ll, node, "minimap")
                nodes.append(node)

            elif ll.keyword("map_loc"):
                nodes.append({"type": "map_loc", "value": ll.require(ll.simple_expression)})
                ll.expect_eol()
                ll.expect_noblock("map_loc")

            elif ll.keyword("show"):
                nodes.append(_explore_parse_show(ll))

            elif ll.keyword("add"):
                node = {"type": "add", "value": ll.require(ll.simple_expression), "props": {}}
                _explore_parse_rest(ll, node, "add")
                nodes.append(node)

            elif ll.keyword("movement"):
                ll.keyword("location")
                node = {"type": "movement", "value": ll.require(ll.simple_expression), "props": {}}
                _explore_parse_rest(ll, node, "movement")
                nodes.append(node)

            elif ll.keyword("interactable"):
                mode = "auto"

                if ll.keyword("label"):
                    mode = "label"
                elif ll.keyword("item"):
                    mode = "item"
                else:
                    ll.keyword("action")

                node = {"type": "interactable", "mode": mode, "value": ll.require(ll.simple_expression), "props": {}}
                _explore_parse_rest(ll, node, "interactable")
                nodes.append(node)

            else:
                ll.error("expected background, minimap, map_loc, show, add, movement, interactable, or if")

    def _explore_parse_location(l):

        name = l.string() or l.word()

        if not name:
            l.error("expected a location name")

        data = {"name": name, "background": None, "nodes": []}

        while not l.match(r':'):
            if l.keyword("background"):
                data["background"] = l.require(l.simple_expression)
            else:
                l.error("expected background or ':'")

        l.expect_eol()
        l.expect_block("location")

        _explore_parse_children(l.subblock_lexer(), data["nodes"])

        return data

    def _explore_walk_all(nodes):
        """
        Yields every node, inside every branch, regardless of conditions.
        """

        for n in nodes:
            yield n
            if n["type"] == "if":
                for _cond, children in n["branches"]:
                    yield from _explore_walk_all(children)

    def _explore_execute_location(data):
        name = data["name"]

        if name in _explore_registry:
            renpy.error(f"location {name!r} is defined more than once")

        by_id = []

        for n in _explore_walk_all(data["nodes"]):
            if n["type"] in _EXPLORE_INDEXED:
                n["id"] = len(by_id)
                by_id.append(n)

        data["by_id"] = by_id
        _explore_registry[name] = data

    def _explore_lint_location(data):

        name = data["name"]

        for n in _explore_walk_all(data["nodes"]):

            if n["type"] not in ("movement", "interactable"):
                continue

            expr = n["value"].strip()

            # Only check literal strings; anything else could have side effects.
            if expr[:1] not in ("'", '"'):
                continue

            try:
                value = renpy.python.py_eval(expr)
            except Exception:
                continue

            if n["type"] == "movement":
                if value not in _explore_registry and not renpy.has_screen(value):
                    renpy.error(f"location {name!r}: movement to unknown location {value!r}")

            elif n["mode"] == "label" and not renpy.has_label(value):
                renpy.error(f"location {name!r}: interactable label {value!r} does not exist")

    renpy.register_statement(
        "location",
        parse=_explore_parse_location,
        execute=_explore_execute_location,
        lint=_explore_lint_location,
        init=True,
        block=True,
        )
