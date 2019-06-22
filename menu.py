from tkinter import Menubutton
from tkinter import scrolledtext
from tkinter import messagebox
import random
from tkinter import filedialog as fldlg
import configparser as cfgparser
from scp import SCPClient
from paramiko import SSHClient
from paramiko import AutoAddPolicy
import tkinter as tk
from tkinter import ttk
from settings import *
import os


def findtextmatches(scr, regexs, regexscolours):
    """
    This function gets the number of matches for each regex
    :return: A dictionary containing the regex name and the number of matches for that regex
    """
    count = tk.IntVar()
    numberofmatches = regexs.copy()

    for regex in numberofmatches:
        numberofmatches[regex] = 0
    for tag in scr.tag_names():
        scr.tag_delete(tag)
        if tag != "sel" and tag != "selected_text":
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
            numberofmatches[regex] = len(scr.tag_ranges(regex)) / 2
    return numberofmatches


class TabSelector:
    """
    This class is used to have multiple logs in screen and display them
    """
    def __init__(self, parent):
        self.parent = parent.tabframe
        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(expand=tk.YES, fill=tk.BOTH)
        self.regexs = regexs
        self.notebook.bind("<<NotebookTabChanged>>", lambda interruptinfo: refreshmatches(parent))

    def addtab(self, tabname):
        scr = scrolledtext.ScrolledText(self.notebook, bg='BLACK', fg='WHITE', font=('consolas', '10'))
        # Create the colors for each filter
        self.notebook.add(scr, text=tabname)
        for regex in regexscolours:
            scr.tag_configure(regex, background=regexscolours[regex][0], foreground=regexscolours[regex][1])

    def changeactualtabname(self, newname):
        self.notebook.tab(self.notebook.index(self.notebook.select()), text=newname)

    def loadlogintoscroll(self, logname):
        """
        Given a logfile name this will read it and display it in tho the scrolltext widget
        :param logname: The name of the log
        """
        actual_tab_scr = self.actualtabobject()
        self.notebook.tab(self.notebook.select(), text=logname)
        file = open(logname, 'r')
        filecontent = file.read()
        actual_tab_scr.config(state=tk.NORMAL)
        actual_tab_scr.delete("1.0", tk.END)
        actual_tab_scr.insert("1.0", filecontent)
        actual_tab_scr.config(state=tk.DISABLED)
        findtextmatches(actual_tab_scr, self.regexs, regexscolours)

    def erasetab(self):
        actual_tab_scr = self.actualtabobject()
        actual_tab_scr.master.destroy()

    def actualtabobject(self):
        """
        This metod return the scrolled text associated with the actual tab selected, if there is no tab, returns None
        :return:
        """
        try:
            return self.notebook.children[self.notebook.select().split(".")[-1]].children['!scrolledtext']
        except Exception:
            return None

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
        self.selectedsection = ""
        sections = self.sections = self.remoteconfargumentreader()
        top = self.top = tk.Toplevel(parent)
        inputsection = self.inputsection = tk.Frame(top)  # The section containing the input entries

        # Create the list to select type of log to retrieve and the subsequent menu
        selectsection = tk.Frame(top)
        listbox = self.listbox = ttk.Combobox(selectsection, state="readonly")
        listbox['values'] = [section for section in sections]
        tk.Label(selectsection, text="Select log:").grid(row=0, column=0, padx=8, pady=2)
        listbox.grid(row=0, column=1, padx=8, pady=2)
        selectsection.grid(row=0)
        self.top.bind("<<ComboboxSelected>>", self.updatesectionselect)
        inputsection.grid(row=1)
        buttonpart = self.buttonpart = tk.Frame(top)  # The part contaning the buttons
        buttonpart.grid(row=2)

    def updatesectionselect(self, change):
        [child.destroy() for child in self.inputsection.winfo_children()]
        [child.destroy() for child in self.buttonpart.winfo_children()]
        i = 4  # Auxiliary variable
        for arg in self.sections[change.widget.get()]:
            if arg == '':
                tk.Label(self.inputsection, text="No input needed").pack()
            else:
                tk.Label(self.inputsection, text=arg).grid(column=0, row=i, padx=8, pady=2)
                tk.Entry(self.inputsection).grid(column=1, row=i, padx=8, pady=2)
                i = i + 1
        tk.Button(self.buttonpart, text="OK", width=10, command=self.returnvalues).grid(row=i, column=0, padx=8, pady=2)
        tk.Button(self.buttonpart, text="CANCEL", width=10, command=self.destroywindow).grid(row=i, column=1, padx=8,
                                                                                             pady=2)
    def returnvalues(self):
        """
        This function is called by the OK button on the menu and it just stores the given values in RemoteDialog
        into a dictionary, save it to the values attribute and then destroy the remotedialog window.
        """
        dicttoreturn = {}
        childrens = self.inputsection.winfo_children()
        if len(childrens) > 1:
            for i in range(0, len(childrens), 2):
                dicttoreturn[childrens[i].cget("text")] = childrens[i+1].get()
        self.values = dicttoreturn
        self.selectedsection = self.listbox.get()
        self.destroywindow()

    def getvalues(self):
        """
        Returns the dictionary containing the given values in the dialog
        :return: The dictionary containing the values
        """
        return self.values, self.selectedsection

    def destroywindow(self):
        """
        Destroy the remotedialog window
        """
        self.top.destroy()

    def remoteconfargumentreader(self):
        """
        This function read the remote.cnf into a dictionary that holds all the possible variables for each section,
        in the keys of the dictionary lies the different sections, the values are tuples containing the different
        variables. It skips the general section.
        :return: The dictionary with arguments tuples.
        """
        sections = {}
        cfgfile = cfgparser.ConfigParser()
        cfgfile.read(cnfdir + '\\remote.cnf')
        for section in cfgfile.sections():
            if section == 'GENERAL':
                continue
            transitional = cfgfile[section]["args"].split(",")
            if len(transitional) > 1:
                try:
                    transitional.remove('')
                except ValueError:
                    pass
            sections[section] = transitional
        return sections


def remoteconfgeneralreader():
    """
    Reads all the general attributes inside the general section into a dictionary, where the keys are the
    attribute names and the values are their respective values.
    :return: The dictionary with attributes values
    """
    attributelist = {}
    cfgfile = cfgparser.ConfigParser()
    cfgfile.read(cnfdir + '\\remote.cnf')
    for attribute in cfgfile["GENERAL"].keys():
        attributelist[attribute] = cfgfile["GENERAL"][attribute]
    return attributelist


def scpgetremotelocalization(section, dictval):
    """
    Given a dictionary with the parameters for scp loading, constructs the remote localization
    and return the string with it.
    :param dictval: The dictionary with the parameters
    :return: The string with the localization within remote PC
    """
    cfgfile = cfgparser.ConfigParser()
    cfgfile.read(cnfdir + '\\remote.cnf')
    stringtosub = cfgfile[section]['REMOTELOCALIZATION']
    for key in dictval:
        stringtosub = stringtosub.replace("[" + key + "]", dictval[key])
    return stringtosub


def scpremotecommandexec(section, dictval):
    """
    Given a dictionary with the parameters for scp loading, constructs the remote localization
    and return the string with it.
    :param dictval: The dictionary with the parameters
    :return: The string with the localization within remote PC
    """
    cfgfile = cfgparser.ConfigParser()
    cfgfile.read(cnfdir + '\\remote.cnf')
    stringtosub = cfgfile[section]['COMMANDS']
    for key in dictval:
        stringtosub = stringtosub.replace("[" + key + "]", dictval[key])
    return stringtosub


class MainMenu:
    """
    The main menu class
    """
    def __init__(self, regexs):
        """
        The regexs to use in this session
        :param regexs: A dictionary as described in settings.py
        """
        global regexscolours
        global win
        # Create the colors for the regexs
        regexscolours = {}
        for regex in regexs:
            ct = [random.randrange(256) for x in range(3)]
            brightness = int(round(0.299 * ct[0] + 0.587 * ct[1] + 0.114 * ct[2]))
            ct_hex = "%02x%02x%02x" % tuple(ct)
            bg_colour = '#' + "".join(ct_hex)
            fg = 'White' if brightness < 120 else 'Black'  # If brightness is too high foreground will be black
            regexscolours[regex] = (bg_colour, fg)
        # Create the main window
        self.win = win = tk.Tk()
        self.win.geometry("1600x800+50+50")
        self.win.title("LogVisualizer")
        self.tabframe = tk.Frame(win)
        self.bottom_frame = tk.Frame(win)
        self.tabsection = TabSelector(self)
        # Draw the menubar
        menu_bar = tk.Menu(win, tearoff=0)
        win.config(menu=menu_bar)
        # Add a cascade for the file managing
        file_cascade = tk.Menu(menu_bar, tearoff=0)
        file_cascade.add_command(label="Open file", command=self.promptlocalfileloader)
        file_cascade.add_command(label="Open remote file", command=self.promptremotefileloader)
        file_cascade.add_separator()
        file_cascade.add_command(label="Quit", command=win.destroy)

        menu_bar.add_cascade(label="File", menu=file_cascade)

        # Draw the filters and tab control on the left side of the window
        self.leftframe = tk.Frame(win)
        addbutton = tk.Button(self.leftframe, text="Add", padx=8, command=lambda: self.tabsection.addtab("Empty"))
        erasebutton = tk.Button(self.leftframe, text="Del", padx=8, command=lambda: self.tabsection.erasetab())
        self.leftframe.pack(side=tk.LEFT)
        addbutton.grid(row=1, column=0)
        erasebutton.grid(row=1, column=1)
        todraw = []
        cascades = []
        buttons = []
        self.filter_menu_frame = tk.Frame(self.leftframe, relief=tk.RAISED, bd=2)
        self.filter_menu_frame.grid(row=2, columnspan=2, ipady=220, ipadx=21)

        filter_menu = Menubutton(self.filter_menu_frame, text="Filters")
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
            exec(parent + ".add_command(label = filtername, command = lambda self=self: alternateregex(self, %s))" % i)
            i = i + 1

        filter_menu.pack(expand=tk.YES, fill=tk.BOTH)
        self.tabframe.pack(expand=tk.YES, fill=tk.BOTH)

        bottom_frame = tk.Frame(win)
        bottom_frame.pack(side=tk.BOTTOM)
        self.tabsection.addtab("Empty")

    def navigatematches(self, regex):
        """
        Navigate through the matches for a given regex name.
        Throws an exectipon if can't find a match for that regex
        :param regex: The name of the regex to find
        """
        scr = self.tabsection.actualtabobject()
        # Highlight colour is black foreground with white background
        try:
            scr.tag_delete('selected_text')
        except:
            pass
        scr.tag_configure('selected_text', background='White', foreground='Black')
        tag_mactches = {}
        tags = scr.tag_names()
        for tag in tags:
            tag_mactches[tag] = scr.tag_ranges(tag)
        index = regexindex[regex]
        try:
            scr.tag_add("selected_text", tag_mactches[regex][index], tag_mactches[regex][index+1])
            scr.see(tag_mactches[regex][index])
            regexindex[regex] = index + 2
            if regexindex[regex] >= len(tag_mactches[regex]):
                regexindex[regex] = 0
        except Exception as e:
            print("Can't find a match for that regex %s" % regex)
            print(str(e))

    def promptlocalfileloader(self):
        """
        Show a explorer for files to find the local log
        """
        ftypes = [('Log files', '*.log'), ('All files', '*')]
        dlg = fldlg.Open(self.win, filetypes=ftypes)
        fl = dlg.show()

        if fl != '':
            self.tabsection.loadlogintoscroll(fl)

    def promptremotefileloader(self):
        """
        Prompt the remotedialog menu by calling the RemoteDialog class and retrieves the information to display the log
        on the scrolltext
        """
        remotewindow = RemoteDialog(self.win)
        self.win.wait_window(remotewindow.top)
        fromwindow = remotewindow.getvalues()  # This gets both, the selected section and the value of the arguments
        values = fromwindow[0]
        section = fromwindow[1]
        cfgfile = cfgparser.ConfigParser()
        cfgfile.read(cnfdir + '\\remote.cnf')
        if section == '':
            return
        sectiondict = cfgfile[section]
        general = remoteconfgeneralreader()
        try:
            ip = sectiondict['ip']
        except Exception:
            ip = general['ip']
        try:
            ssh = SSHClient()
            ssh.set_missing_host_key_policy(AutoAddPolicy)
            ssh.connect(ip, username=general['user'], password=general['password'])
        except Exception as e:
            print("Exception: ", str(e))
            messagebox.showerror("Error", "Can't connect to remote")
        else:
            if sectiondict['method'] == 'SCP':
                try:
                    scp = SCPClient(ssh.get_transport())
                    remoteloc = scpgetremotelocalization(section, values)
                    scp.get(remoteloc, 'remote.log')
                    self.tabsection.loadlogintoscroll('remote.log')
                    os.remove('remote.log')
                except Exception as e:
                    print("Caught exception: ", str(e))
                    messagebox.showerror("Error", "Can't find the remote log")
            if sectiondict['method'] == 'SSH':
                try:
                    remotecommand = scpremotecommandexec(section, values)
                    result = ssh.exec_command(remotecommand)
                    with open('remote.log', 'w') as file:
                        file.write(result[1].read().decode('utf-8'))
                    self.tabsection.loadlogintoscroll('remote.log')
                    os.remove('remote.log')
                except Exception as e:
                    print("Caught exception: ", str(e))
                    messagebox.showerror("Error", "Can't execute the commands")



def alternateregex(mainmenu, regexn):
    """
    Alternate the state for the filter for a given the number of the selected regex in the regexs dictionary
    :param regexn: The regex position in the regexs dictionary
    """
    regexkey = list(regexs.keys())[regexn]
    regexsfilter[regexkey] = not regexsfilter[regexkey]
    refreshmatches(mainmenu)


def refreshmatches(mainmenu):
    mainmenu.bottom_frame.destroy()
    mainmenu.bottom_frame = tk.Frame(win)
    mainmenu.bottom_frame.pack(side=tk.BOTTOM)
    actual_tab = mainmenu.tabsection.actualtabobject()
    if actual_tab is None:
        return
    numberofmatches = findtextmatches(actual_tab, regexs, regexscolours)
    for regex in regexsfilter:
        if regexsfilter[regex]:
            print()
            button_category = tk.Button(mainmenu.bottom_frame,
                                        text=regex
                                        .replace("_", "/").replace("·", "/")+"(%s)" % numberofmatches[regex],
                                        background=regexscolours[regex][0],
                                        foreground=regexscolours[regex][1],
                                        command=lambda regex=regex: mainmenu.navigatematches(regex))
            button_category.pack(side=tk.LEFT)