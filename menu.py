from tkinter import Menubutton
from tkinter import scrolledtext
import random
from tkinter import filedialog as fldlg
import configparser as cfgparser
from scp import SCPClient
from paramiko import SSHClient
from paramiko import AutoAddPolicy
import tkinter as tk
from settings import *


def remoteconfargumentreader():
    """
    This function read the remote.cnf into a dictionary that holds all the possible variables for each section,
    in the keys of the dictionary lies the different sections, the values are tuples containing the different
    variables. It skips the general section.
    :return: The dictionary with arguments tuples.
    """
    argumentlist = {}
    cfgfile = cfgparser.ConfigParser()
    cfgfile.read('remote.cnf')
    for section in cfgfile.sections():
        if section == 'GENERAL':
            continue
        argumentlist[section] = cfgfile[section]["ARGS"].split(",")
    return argumentlist


def remoteconfgeneralreader():
    """
    Reads all the general attributes inside the general section into a dictionary, where the keys are the
    attribute names and the values are their respective values.
    :return: The dictionary with attributes values
    """
    attributelist = {}
    cfgfile = cfgparser.ConfigParser()
    cfgfile.read('remote.cnf')
    for attribute in cfgfile["GENERAL"].keys():
        attributelist[attribute] = cfgfile["GENERAL"][attribute]
    return attributelist


class RemoteDialog:
    """
    This class holds the dialog for getting the variables when asking for a remote log file.
    """
    def __init__(self, parent):
        """
        The constructor for the Remote Dialog class
        :param parent: The parent window that will have this remotedialog menu
        """
        self.values = {}
        args = remoteconfargumentreader()
        top = self.top = tk.Toplevel(parent)
        inputsection = self.inputsection = tk.Frame(top)  # The section containing the input entries
        i = 4  # Auxiliary variable
        for arg in args['SCP']:  # For now is hardcoded to SCP
            tk.Label(inputsection, text=arg).grid(column=0, row=i, padx=8, pady=2)
            tk.Entry(inputsection).grid(column=1, row=i, padx=8, pady=2)
            i = i + 1
        inputsection.grid(row=0)

        buttonpart = self.buttonpart = tk.Frame(top)  # The part contaning the buttons
        tk.Button(buttonpart, text="OK", width=10, command=self.returnvalues).grid(row=i, column=0, padx=8, pady=2)
        tk.Button(buttonpart, text="CANCEL", width=10, command=self.destroywindow).grid(row=i, column=1, padx=8, pady=2)
        buttonpart.grid(row=2)

    def returnvalues(self):
        """
        This function is called by the OK button on the menu and it just stores the given values in RemoteDialog
        into a dictionary, save it to the values attribute and then destroy the remotedialog window.
        """
        dicttoreturn = {}
        childrens = self.inputsection.winfo_children()
        for i in range(0, len(childrens), 2):
            dicttoreturn[childrens[i].cget("text")] = childrens[i+1].get()
        self.values = dicttoreturn
        self.destroywindow()

    def getvalues(self):
        """
        Returns the dictionary containing the given values in the dialog
        :return: The dictionary containing the values
        """
        return self.values

    def destroywindow(self):
        """
        Destroy the remotedialog window
        """
        self.top.destroy()


def findtextmatches():
    """
    This function gets the number of matches for each regex
    :return: A dictionary containing the regex name and the number of matches for that regex
    """
    global regexscolours
    global regexsfilter
    global regexs
    global scr
    count = tk.IntVar()
    numberofmatches = regexs.copy()

    for regex in numberofmatches:
        numberofmatches[regex] = 0
    for tag in scr.tag_names():
        scr.tag_delete(tag)
        if tag != "sel":
            scr.tag_configure(tag, background=regexscolours[tag][0], foreground=regexscolours[tag][1])

    for regex in regexs:
        start = 1.0
        if not regexsfilter[regex]:
            continue
        while 1:
            pos = scr.search(regexs[regex], start, stopindex=tk.END, count=count, regexp=regexs[regex])
            if pos == '':
                break
            start = pos + "+%sc" % count.get()
            scr.tag_add(regex, pos, pos + "+%sc" % count.get())
            numberofmatches[regex] = len(scr.tag_ranges(regex))/2
    return numberofmatches


def navigatematches(regex):
    """
    Navigate through the matches for a given regex name.
    Throws an exectipon if can't find a match for that regex
    :param regex: The name of the regex to find
    """
    global scr
    global regexindex
    tag_mactches = {}
    tags = scr.tag_names()
    for tag in tags:
        tag_mactches[tag] = scr.tag_ranges(tag)
    index = regexindex[regex]
    print("Actual index %s " % index)
    try:
        scr.see(tag_mactches[regex][index])
        print(tag_mactches[regex][index])
        regexindex[regex] = index + 2
        if regexindex[regex] >= len(tag_mactches[regex]):
            regexindex[regex] = 0
    except:
        print("Can't find a match for that regex %s" % regex)


def loadlogintoscroll(logname):
    """
    Given a logfile name this will read it and display it in tho the scrolltext widget
    :param logname: The name of the log
    """
    global scr
    file = open(logname, 'r')
    filecontent = file.read()
    scr.delete("1.0", tk.END)
    scr.config(state=tk.NORMAL)
    scr.insert("1.0", filecontent)
    scr.config(state=tk.DISABLED)
    findtextmatches()


def alternateregex(regexn):
    """
    Alternate the state for the filter for a given the number of the selected regex in the regexs dictionary
    :param regexn: The regex position in the regexs dictionary
    """
    global bottom_frame
    global regexsfilter
    global win
    regexkey = list(regexs.keys())[regexn]
    regexsfilter[regexkey] = not regexsfilter[regexkey]
    bottom_frame.destroy()
    bottom_frame = tk.Frame(win)
    bottom_frame.pack(side=tk.BOTTOM)
    numberofmatches = findtextmatches()
    for regex in regexsfilter:
        if regexsfilter[regex]:
            print()
            button_category = tk.Button(bottom_frame,
                                        text=regex
                                        .replace("_", "/").replace("·", "/")+"(%s)" % numberofmatches[regex],
                                        background=regexscolours[regex][0],
                                        foreground=regexscolours[regex][1],
                                        command=lambda regex=regex: navigatematches(regex))
            button_category.pack(side=tk.LEFT)


def promptlocalfileloader():
    """
    Show a explorer for files to find the local log
    """
    ftypes = [('Log files', '*.log'), ('All files', '*')]
    dlg = fldlg.Open(win, filetypes=ftypes)
    fl = dlg.show()

    if fl != '':
        loadlogintoscroll(fl)


def scpgetremotelocalization(dictval):
    """
    Given a dictionary with the parameters for scp loading, constructs the remote localization
    and return the string with it.
    :param dictval: The dictionary with the parameters
    :return: The string with the localization within remote PC
    """
    cfgfile = cfgparser.ConfigParser()
    cfgfile.read('remote.cnf')
    stringtosub = cfgfile['SCP']['REMOTELOCALIZATION']
    for key in dictval:
        stringtosub = stringtosub.replace("[" + key + "]", dictval[key])
    return stringtosub


def promptremotefileloader():
    """
    Prompt the remotedialog menu by calling the RemoteDialog class and retrieves the information to display the log
    on the scrolltext
    """
    remotewindow = RemoteDialog(win)
    win.wait_window(remotewindow.top)
    values = remotewindow.getvalues()
    option = 'SCP'
    general = remoteconfgeneralreader()
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy)
    ssh.connect(general['ip'], username=general['user'], password=general['password'])
    if option == 'SCP':
        scp = SCPClient(ssh.get_transport())
        scpgetremotelocalization(values)
        scp.get('readme.txt', 'remote.log')
        loadlogintoscroll('remote.log')


class MainMenu:
    """
    The main menu class
    """
    def __init__(self, regexs):
        """
        The regexs to use in this session
        :param regexs: A dictionary as described in settings.py
        """
        global bottom_frame
        global scr
        global regexscolours
        global win
        # Create the main window
        self.win = win = tk.Tk()
        self.win.geometry("1600x800+50+50")
        self.win.title("LogVisualizer")

        # Draw the menubar
        menu_bar = tk.Menu(win, tearoff=0)
        win.config(menu=menu_bar)
        # Add a cascade for the file managing
        file_cascade = tk.Menu(menu_bar, tearoff=0)
        file_cascade.add_command(label="Open file", command=promptlocalfileloader)
        file_cascade.add_command(label="Open remote file", command=promptremotefileloader)
        file_cascade.add_separator()
        file_cascade.add_command(label="Quit", command=win.destroy)

        menu_bar.add_cascade(label="File", menu=file_cascade)

        # Draw the filters control on the left side of the window
        todraw = []
        cascades = []
        buttons = []
        filter_menu = Menubutton(win, text="Filters")
        topmenu = tk.Menu(filter_menu, tearoff=True)
        filter_menu.configure(menu=topmenu)

        for path in regexs:
            for submenu in range(len(path.split("_"))):
                todraw.append("_".join(path.split("_")[:submenu+1]))
        todraw = list(dict.fromkeys(todraw).keys())
        todraw.remove("")
        # Separate cascades from final buttons
        for element in todraw:
            if "·" in element:
                buttons.append(element)
                cascades.append("_".join(element.split("·")[:-1]))
            else:
                cascades.append(element)
        cascades = list(dict.fromkeys(cascades).keys())
        cascades.sort()
        # Draw submenus with cascades
        for cascade in cascades:
            splitted = cascade.split("_")
            if len(splitted) == 2:
                exec("_" + splitted[-1] + " = tk.Menu(topmenu)")
                exec("topmenu.add_cascade(label=splitted[-1], menu=" + "_" + splitted[-1] + ")")
            else:
                parent = "_".join(splitted[:-1])
                actual = "_".join(splitted)
                exec(actual + " =  tk.Menu(" + parent + ")")
                exec(parent + ".add_cascade(label=splitted[-1], menu=" + actual + ")")

        i = 0 # Auxiliary variable
        for filter in buttons:
            splitted = filter.split("·")
            parent = splitted[0]
            filtername = splitted[1]
            exec(parent + ".add_command(label = filtername, command = lambda : alternateregex(%s))" % i)
            i = i + 1

        filter_menu.pack(side=tk.LEFT)

        # Draw the area where the log is going to be written
        scr = scrolledtext.ScrolledText(win, bg='BLACK', fg='WHITE')
        scr.pack(expand=tk.YES, fill=tk.BOTH)
        # Create the colors for each filter
        for regex in regexs:
            ct = [random.randrange(256) for x in range(3)]
            brightness = int(round(0.299 * ct[0] + 0.587 * ct[1] + 0.114 * ct[2]))
            ct_hex = "%02x%02x%02x" % tuple(ct)
            bg_colour = '#' + "".join(ct_hex)
            fg = 'White' if brightness < 120 else 'Black'  # If brightness is too high foreground will be black
            regexscolours[regex] = (bg_colour, fg)
            scr.tag_configure(regex, background=bg_colour, foreground=fg)
        bottom_frame = tk.Frame(win)
        bottom_frame.pack(side=tk.BOTTOM)