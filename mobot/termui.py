import time
import curses
import atexit

class TerminalApplication():
    def __init__(self):
        self.scr = curses.initscr()
        curses.start_color()
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_WHITE)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
        self.size = self.scr.getmaxyx() # (row, col)
        curses.noecho()
        curses.cbreak()
        # self.scr.nodelay(1)
        self.scr.keypad(1)
        self.scr.border(0)
        self.createMenuBar()

        # loggerPad
        self.loggerPad = self.scr.subwin(self.size[0] // 3, self.size[1] - 6,
            3, 3)
        self.loggerPad.border(0, 0, 1)
        self.loggerPadSize = self.loggerPad.getmaxyx()
        self.scr.addstr(3, 5, "Event Logging Viewer")
        self.logentries = []

        # statusPad
        self.row_b_log = self.loggerPadSize[0] + 4 # Row number below logger
        self.statusPad = self.scr.subwin(self.size[0] // 3, self.size[1] - 6,
            self.row_b_log, 3)
        self.statusPad.border(0, 0, 1)
        self.statusPadSize = self.statusPad.getmaxyx()
        self.scr.addstr(self.row_b_log, 5, "Mobot Status Viewer")

        self.refreshAll()

    def createMenuBar(self):
        self.scr.addstr(0, 1, " " * (self.size[1] - 2), curses.A_REVERSE)
        self.scr.addstr(0, 2, "Mobot Terminal Monitor v1.0 alpha",
            curses.A_REVERSE)

    def refreshAll(self):
        self.scr.erase()

        self.scr.border(0)
        self.createMenuBar()

        self.loggerPad.erase()
        self.loggerPad.border(0, 0, 1)

        self.scr.addstr(3, 5, "Event Logging Viewer")

        self.statusPad = self.scr.subwin(self.size[0] // 3, self.size[1] - 6,
            self.row_b_log, 3)
        self.statusPad.border(0, 0, 1)

        self.scr.addstr(self.row_b_log, 5, "Mobot Status Viewer")

        samp = {1: '[WARN]', 2: '[INIT]', 3: '[INFO]', 4: '[INFO]'}
        i = 2
        for entry in self.logentries:
            self.loggerPad.addstr(i, 2, str(entry[2]))
            self.loggerPad.addstr(i, 2 + 9, samp[entry[0]],
                curses.color_pair(entry[0]))
            self.loggerPad.addstr(i, 2 + 9 + 7, entry[1],
                curses.color_pair(3))
            i += 1

        self.loggerPad.refresh()
        self.statusPad.refresh()

    def resizeAll(self):
        self.size = self.scr.getmaxyx()
        self.loggerPad.resize(self.size[0] // 3, self.size[1] - 6)
        self.statusPad.resize(self.size[0] // 3, self.size[1] - 6)
        self.loggerPadSize = self.loggerPad.getmaxyx()
        self.row_b_log = self.loggerPadSize[0] + 4
        self.statusPadSize = self.statusPad.getmaxyx()

    def warn(self, msg):
        self.log(msg, 1)

    def init(self, msg):
        self.log(msg, 2)

    def info(self, msg):
        self.log(msg, 4)

    def log(self, text, typ=3):
        first_row = 5 + 1
        last_row = first_row + self.loggerPadSize[0] - 4
        while len(self.logentries) > last_row - first_row - 1:
            self.logentries.pop(0)
        self.logentries.append((typ, text, time.ctime()[11:19]))
        self.refreshAll()

    def updateState(self, states):
        pass

    """
    def mainloop(self):
        while 1:
            c = self.scr.getch()
            if c == curses.KEY_RESIZE:
                self.info("resized")
                self.resizeAll()
            self.refreshAll()
    """

    @atexit.register
    def terminate(self):
        curses.nocbreak()
        self.scr.keypad(1)
        curses.echo()
        curses.endwin()

if __name__ == "__main__":
    app = TerminalApplication()
    app.scr.getch()
    app.mainloop()
