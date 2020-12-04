import os
import sys

chrome_path = "./chromedriver.exe"


try:
    local_path = os.path.join(sys._MEIPASS, chrome_path)
except Exception:
    local_path = chrome_path
