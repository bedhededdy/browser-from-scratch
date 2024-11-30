import sys
import tkinter as tk

from URL import URL
from Browser import Browser

# TODO: EXERCISE 2-5
# TODO: EXERCISE 3-1
# TODO: EXERCISE 4-1

def main():
    if len(sys.argv) < 2:
        url = URL("file://example.html")
    else:
        url = URL(sys.argv[1])
    browser = Browser()
    browser.load(url)
    tk.mainloop()

if __name__ == "__main__":
    main()
