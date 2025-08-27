# Loki's Point-and-Click

[Click here to view my other scripts](https://github.com/Lorekeeper49/Loki-s-Ren-Py-scripts)

## INFORMATION

This is a proper working Point-and-Click system that you can use for certain sections of your Ren'Py game, or you could use it for the entire game too if you want.

If you have any issues or suggestions for what should be added to these scripts and assets or the information area, list them in the issues tab

## Copyright policy

All of my scripts and assets are operated under the same copyright policy: you may use, edit, and redistribute these scripts and assets as you please, the only thing I ask for is that you credit me by name, "Lorekeeper49".  If you don't follow this policy, you can and will get flagged for stealing, so please cooperate and give me some credit for my hard work in making something useful for your games.

## HOW TO USE

Variables:

- The `inventory` list is just about the only list that doesn't reset every new section, check for items in the players inventory for certain conditions
- The `explored` list is reset every new section for explored aspects of that section, add to this for condition checks exclusive to that section for dynamic things
- The `codes` list is reset every new section for the codes of that section, make sure each code is identified properly so no problems appear with other codes

Steps to use:

- Create a new script filled with screens for each location on your map
    - All the screens need to be named the same as the background you use for them without the `bg` prefix, the system will look for both the image and the screen by the same name to easily go between each location
- Call the `explore` label using the name of your first screen
- Call the `next_location` label when you want to advance to the next location using the buttons
- Call the `dialpad` label when you want a code to be inputed to proceed, it is recommended that you call this label with the `If()` action, checking if the code has already been put in before showing it.
    - `c`: the correct code to input
    - `p`: the name of the screen you came into the dialpad from
    - `s`: the name to save into the `codes` list so players won't have to put in the code again.
- Return when you want to end the section
- Note: if you're calling dialogue, make sure you call a screen at the end, if you return at any point during the section, you will return to the point where you called the `explore` label