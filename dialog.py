#!/usr/bin/env python
import Tkinter as tk

class Dialog(object):
    def __init__(self, parent, title = None):
        self.w = tk.Toplevel(parent)
        self.w.transient(parent)
        if title:
            self.w.title(title)
        self.parent = parent
        self.result = None
        body = tk.Frame(self.w)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)
        self.buttonbox()
        if not self.initial_focus:
            self.initial_focus = self
        self.w.protocol("WM_DELETE_WINDOW", self.cancel)
        self.w.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                              parent.winfo_rooty()+50))
        self.initial_focus.focus_set()
        self.w.wait_visibility()
        self.w.grab_set()

    def run(self):
        self.w.wait_window(self.w)

    # construction hooks
    def body(self, master):
        # create dialog body.  return widget that should have
        # initial focus.  this method should be overridden
        pass

    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons
        box = tk.Frame(self.w)
        w = tk.Button(box, text="OK", width=10, command=self.ok, default=tk.ACTIVE)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        w = tk.Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        self.w.bind("<Return>", self.ok)
        self.w.bind("<Escape>", self.cancel)
        box.pack()

    # standard button semantics
    def ok(self, event=None):
        self.w.withdraw()
        self.w.update_idletasks()
        self.cancel()

    def cancel(self, event=None):
        # put focus back to the parent window
        self.parent.focus_set()
        self.w.destroy()


def main():
    root = tk.Tk()
    Dialog(root)
    root.mainloop()

if __name__ == '__main__':
    main()
