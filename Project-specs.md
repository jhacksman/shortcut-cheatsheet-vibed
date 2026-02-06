## Shortcut Cheatsheet Project Specs

### 1. Overview

Shortcut Cheatsheet is desktop application that makes using your computer with a keyboard easier. It does this by displaying keyboard shortcuts for the currently focused application.

The goal is to make using your keyboard easier, so Shortcut Cheatsheet is designed with a keyboard first UI. Everything can be done without a mouse, there are lots of mnemonics, and we use sensical default keybinding.

### 2. Requirements

- The application should run on Ubuntu 24 running Gnome and Wayland.

- The application should assume the user has installed the gnome extension

"window-calls."

* The application should open a cheatsheet window on launch

* There should be a seperate settings window

#### 2.1. Cheatsheet Window Requirements

- Show the shortcuts for the currently focused application, unless the currently focused application is this shortcut cheatsheet application.

- Display shortcuts in a table, with the left column the action, and the right column the key combination for the action.

- Be movable to the 4 corners of the screen with the arrow keys.

- Control font size with ctrl + and ctrl -.

- Have persistent font size between launches.

- Use a dark theme

- Display the application name of the currently focused application in the title bar.

#### 2.2. Settings Window Requirements

- Open when the user presses the s key while the cheatsheet is focused.

- Show an editable table of the shortcuts for the last focused application (that was not this shortcut cheatsheet app)

- Have a delete shortcut button on each row, marked with a red x

- Have a menu to change between the displayed shortcuts of registered applications.

- Have a button to add a new application's shortcuts.

- Opens a menu to select an application from the list of running applications when the add application button is pressed.

- Have a button to delete the entire application shortcut profile.

- Have a button to save the shortcuts and close the settings menu

- Have a button to cancel the changes

- Have all ui elements navigable Tab and Shift + Tab.

- Have all ui elements have a brighter background when they are focused.

- Have all ui elements be accesible with mnenomics

### 3. Documentation resources

- Window calls gnome extensions:

https://github.com/ickyicky/window-calls,

https://extensions.gnome.org/extension/4724/window-calls/

- PyQt6 docs

https://doc.qt.io/qtforpython-6/

### 4. Implementation

- The application should be implemented in Python.

- The application should use PyQt6 for the GUI.

- The code must be readable and maintainable.

- The application must use a virtual environment.

- The logic for getting the currently focused window should be modular to enable easier cross platform support

- The logic for moving the cheatsheet shortcut window should be modular

- The logic for pinning the cheatsheet shortcut window above other applications should be modular

- Avoid common pitfalls
  
  - Not considering the resolution of the display, resulting in moving windows too little or too far
  
  - Not using "xdb_toplevel" to move windows when on Wayland systems
  
  - Searching shortcut records with the title rather than application name of the currently focused window.


