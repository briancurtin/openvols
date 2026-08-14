# TLA+ Specifications

This directory contains [TLA+](https://www.tlapl.us/) specifications for the
Registration and Waitlist system. They're most easily used with the
[VSCode extension](https://github.com/tlaplus/vscode-tlaplus/), which you can
install directly from VSCode's extension panel.

The modules successfully pass with the model checker, `TLC`. I'm still new to TLA+
so they may not be ideal, but I think they do what they're supposed to.

## State Space Visualization

Running `TLC` with the `-dump dot` will output a file that [Graphviz](https://graphviz.org/)
can turn into an image showing all of the states `Next` runs through. You can also explore
this in the debugger if you run `TLC` in debug mode—it'll put a breakpoint on
`Init` and `Next` and you can step through the module from there.

1. Run `TLC` in VSCode with `-workers 1 -coverage 1 -dump dot MODULE_NAME.dot`
2. With Graphviz installed, run `dot -Tpng docs/design/MODULE_NAME.dot -o MODULE_NAMEAME.png`
