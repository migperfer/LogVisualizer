import random
import logjsonreader
import tkinter as tk
from tkinter import Menubutton
from tkinter import scrolledtext
from tkinter import filedialog as fldlg
import configparser as cfgparser
from scp import SCPClient
from paramiko import SSHClient
from paramiko import AutoAddPolicy

def remoteconfargumentreader():
    argumentlist = {}
    cfgfile = cfgparser.ConfigParser()
    cfgfile.read('remote.cnf')
    for section in cfgfile.sections():
        if section == 'GENERAL':
            continue
        argumentlist[section] = cfgfile[section]["ARGS"].split(",")
    return argumentlist


def remoteconfgeneralreader():
    attributelist = {}
    cfgfile = cfgparser.ConfigParser()
    cfgfile.read('remote.cnf')
    for attribute in cfgfile["GENERAL"].keys():
        attributelist[attribute] = cfgfile["GENERAL"][attribute]
    return attributelist


class RemoteDialog:

    def __init__(self, parent):
        self.values = {}
        args = remoteconfargumentreader()
        top = self.top = tk.Toplevel(parent)
        inputsection = self.inputsection = tk.Frame(top)
        i = 4 # Auxiliary variable
        for arg in args['SCP']:
            tk.Label(inputsection, text=arg).grid(column=0, row=i, padx=8, pady=2)
            tk.Entry(inputsection).grid(column=1, row=i, padx=8, pady=2)
            i = i + 1
        inputsection.grid(row=0)

        buttonpart = self.buttonpart = tk.Frame(top)
        tk.Button(buttonpart, text="OK", width=10, command=self.returnvalues).grid(row=i, column=0, padx=8, pady=2)
        tk.Button(buttonpart, text="CANCEL", width=10, command=self.destroywindow).grid(row=i, column=1, padx=8, pady=2)
        buttonpart.grid(row=2)

    def returnvalues(self):
        dicttoreturn = {}
        childrens = self.inputsection.winfo_children()
        for i in range(0, len(childrens), 2):
            dicttoreturn[childrens[i].cget("text")] = childrens[i+1].get()
        self.values = dicttoreturn
        self.destroywindow()

    def getvalues(self):
        return self.values

    def destroywindow(self):
        self.top.destroy()


def findtextmatches():
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
    global scr
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
    global scr
    file = open(logname, 'r')
    filecontent = file.read()
    scr.delete("1.0", tk.END)
    scr.config(state=tk.NORMAL)
    scr.insert("1.0", filecontent)
    scr.config(state=tk.DISABLED)
    findtextmatches()


def alternateregex(regexn):
    global bottom_frame
    global regexsfilter
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
    ftypes = [('Log files', '*.log'), ('All files', '*')]
    dlg = fldlg.Open(win, filetypes=ftypes)
    fl = dlg.show()

    if fl != '':
        loadlogintoscroll(fl)


def scpgetremotelocalization(dictval):
    cfgfile = cfgparser.ConfigParser()
    cfgfile.read('remote.cnf')
    stringtosub = cfgfile['SCP']['REMOTELOCALIZATION']
    for key in dictval:
        stringtosub = stringtosub.replace("[" + key + "]", dictval[key])
    return stringtosub


def promptremotefileloader():
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


def drawmenu(win, regexs):
    global bottom_frame
    global scr
    # Draw the menubar

    menu_bar = tk.Menu(win, tearoff=0)
    win.config(menu=menu_bar)

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

    for regex in regexs:
        ct = [random.randrange(256) for x in range(3)]
        brightness = int(round(0.299 * ct[0] + 0.587 * ct[1] + 0.114 * ct[2]))
        ct_hex = "%02x%02x%02x" % tuple(ct)
        bg_colour = '#' + "".join(ct_hex)
        fg = 'White' if brightness < 120 else 'Black'
        regexscolours[regex] = (bg_colour, fg)
        scr.tag_configure(regex, background=bg_colour, foreground=fg)
    bottom_frame = tk.Frame(win)
    bottom_frame.pack(side=tk.BOTTOM)

if __name__ == '__main__':
    regexs = logjsonreader.readjson("logparser.json")
    regexscolours = {}
    regexsfilter = regexs.copy()
    for regex in regexsfilter:
        regexsfilter[regex] = False
    regexindex = regexs.copy()
    for regex in regexindex:
        regexindex[regex] = 0

    win = tk.Tk()
    win.geometry("1600x800+50+50")
    drawmenu(win, regexs)
    win.title("LogVisualizer")
    win.mainloop()