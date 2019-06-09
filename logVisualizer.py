import menu
from settings import *

if __name__ == '__main__':
    """
    It's the main module, it just import the settings, initialize some variables and create the main menu.
    """
    for regex in regexsfilter:
        regexsfilter[regex] = False  # This line is to make sure that at the beginning no filter is active
    for regex in regexindex:
        regexindex[regex] = 0  # This line is to make sure that every index of matches start at the first one

    main_menu = menu.MainMenu(regexs)
    main_menu.win.mainloop()