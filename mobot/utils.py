import subprocess
import time
from easyterm import TerminalController

term = TerminalController()

def null(*args, **kwargs):
    pass

def init(msg):
    print time.ctime()[11:19], \
        term.render("${GREEN}${BG_WHITE}[INIT]${NORMAL}"), \
        term.render("${YELLOW}%s${NORMAL}"%msg)

def info(msg):
    print time.ctime()[11:19], \
        term.render("${GREEN}[INFO]${NORMAL}"), \
        term.render("${YELLOW}%s${NORMAL}"%msg)

def warn(msg):
    print time.ctime()[11:19], \
        term.render("${RED}${BG_WHITE}[WARN]${NORMAL}"), \
        term.render("${RED}%s${NORMAL}"%msg)

def speak(text, block=False):
    proc = subprocess.Popen(["say", "-v", "Samantha", text])
    if block: proc.wait()

def speaklog(text, block=False):
    info(text)
    speak(text, block)

# Test if platform supports voice synthesizer
try:
    speak("")
except:
    speak = null

if __name__ == "__main__":
    speak("Hello world!")
    speaklog("This is a logged example")
    info("This is just a logging example")
