import menu
from settings import *

if __name__ == '__main__':
    for regex in regexsfilter:
        regexsfilter[regex] = False
    for regex in regexindex:
        regexindex[regex] = 0

    main_menu = menu.MainMenu(regexs)
    main_menu.win.mainloop()