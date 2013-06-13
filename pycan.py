#!/usr/bin/env python
import Tkinter as tk
import ttk
import tkMessageBox
import tkFileDialog
import tkFont
import canchannel
import kvaser
import canmsg
import os

channel_types = [canchannel.CanChannel, kvaser.KvaserCanChannel, canchannel.CanChannel]

class Logger(ttk.Frame):
    def __init__(self, master=None):
        ttk.Frame.__init__(self, master=master)
        self.messages = []
        self.font = tkFont.Font(family='monospace')
        self.line_height = int(self.font.metrics('linespace'))
        self.no_of_lines = 0
        self.text = tk.Text(self, font=self.font)
        self.text.bind('<Configure>', self.handle_configure)
        self.text.pack(side=tk.LEFT, expand=True, fill="both")
        scrbar = tk.Scrollbar(self)
        scrbar.pack(side=tk.RIGHT, fill=tk.Y)
        scrbar.config(command=self.scroll)
        self.text.config(yscrollcommand = scrbar.set)
        self.row = 0
        self.auto_scroll = tk.IntVar()
        self.auto_scroll.set(1)
        self.changed = False
        self.create_menu()
        self.poll()

    def handle_configure(self, event):
        self.no_of_lines = event.height / self.line_height

    def create_menu(self):
        self.popup_menu = tk.Menu(self, tearoff=0)
        self.popup_menu.add_command(label='something'
                , command=self.do_something)
        self.text.bind('<Button-3>', self.do_popup_menu)

    def do_popup_menu(self, event):
        self.popup_menu.post(event.x_root - 5, event.y_root)

    def do_something(self):
        self.log('Did something')
        self.log(str(self.font.actual()))

    def save(self, filename):
        self.log('Save: ' + filename)
        self.changed = False

    def poll(self):
        fmt = "{1:5d}: {0}\n"
        count = len(self.messages)
        start = count - self.no_of_lines
        if count > self.no_of_lines:
            count = self.no_of_lines
        for i, m in enumerate(self.messages[start:start+count]):
            self.text.insert(i, fmt.format(str(m), start + i))
        self.after(300, self.poll)

    def scroll(self, *args):
        print self.no_of_lines, args

    def log(self, m):
        self.changed = True
        self.messages.append(m)
        #self.text.insert(tk.END, "{1:5d}: {0}\n".format(str(m), self.row))

class PyCan(tk.Tk):
    def __init__(self, channel=0):
        tk.Tk.__init__(self)
        self.channel = channel
        self.idfmt = tk.IntVar()
        self.idfmt.set(canmsg.FORMAT_STD)
        self.title('PyCAN')
        self.logger = Logger(self)
        self.logger.pack(expand=True, fill="both")
        self.channel_setup()
        self.create_menu()
        self.poll()

    def channel_setup(self):
        ct = [object] + channel_types
        for d in ct:
            name = d.__name__
            try:
                driver = d(channel=self.channel, logger=self.logger)
                break
            except Exception as e:
                fmt = 'Failed starting driver: {}: {}'
                s = fmt.format(name, str(e)) 
                self.logger.log(s)
        fmt = 'Using driver: {}'
        s = fmt.format(driver.__class__.__name__)
        self.logger.log(s)
        self.driver = driver

    def create_menu(self):
        menu = tk.Menu(self)
        self.config(menu=menu)
        filemenu = tk.Menu(menu, tearoff=0)
        filemenu.add_command(label='Save', underline=0,
                accelerator='C-s', command=self.do_save)
        self.bind_all('<Control-Key-s>', self.do_save)
        filemenu.add_command(label='Exit', underline=1,
                accelerator='C-q', command=self.do_quit)
        self.bind_all('<Control-Key-q>', self.do_quit)
        menu.add_cascade(label='File', underline=0, menu=filemenu)
        settingsmenu = tk.Menu(menu, tearoff=0)
        settingsmenu.add_checkbutton(label='stcan format', underline=1
                , variable=self.idfmt
                , onvalue=canmsg.FORMAT_STCAN, offvalue=canmsg.FORMAT_STD
                , command=self.id_format)
        settingsmenu.add_checkbutton(label='autoscroll', underline=0
                , variable=self.logger.auto_scroll)
        menu.add_cascade(label='Settings', underline=0, menu=settingsmenu)
        actionmenu = tk.Menu(menu)
        actionmenu.add_command(label='Send', command=self.send)
        menu.add_cascade(label='Action', underline=0, menu=actionmenu)

    def do_save(self, *args):
        fn = tkFileDialog.asksaveasfilename(initialdir=os.getcwd())
        self.logger.save(fn)

    def send(self):
        m = canmsg.CanMsg()
        m.addr = 60
        m.group = canmsg.GROUP_PIN
        m.type = canmsg.TYPE_IN
        m.data = [8,7,6,5,4,3,2,1]
        self.driver.write(m)

    def id_format(self):
        canmsg.format_set(self.idfmt.get())
        
    def do_quit(self, *args):
        self.driver.close()
        self.quit()

    def poll(self):
        m = self.driver.read()
        while m:
            self.logger.log(m)
            m = self.driver.read()
        self.after(10, self.poll)

def main(channel):
    app = PyCan(channel)
    app.mainloop()

if __name__ == '__main__':
    try:
        ch = int(sys.argv[1])
    except:
        ch = 0
    try:
        main(ch)
    except KeyboardInterrupt:
        pass

