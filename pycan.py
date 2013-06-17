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

channel_types = ((canchannel.CanChannel, (0,))
        , (kvaser.KvaserCanChannel, (0, 1)))

class Logger(ttk.Frame):
    def __init__(self, master=None):
        ttk.Frame.__init__(self, master=master)
        self.fmt = "{1:5d}: {0}\n"
        self.messages = []
        self.count = len(self.messages)
        self.font = tkFont.Font(family='monospace')
        self.line_height = int(self.font.metrics('linespace'))
        self.no_of_lines = 0
        self.text = tk.Text(self, font=self.font)
        self.bind('<Configure>', self.handle_configure)
        self.text.bind('<Button-1>', lambda x: None)
        self.text.bind('<Button-2>', lambda x: None)
        self.text.bind('<Button-3>', self.do_popup_menu)
        self.text.bind('<Button-4>', self.wheel_up)
        self.text.bind('<Button-5>', self.wheel_down)
        self.text.bind('<KeyPress>', self.handle_keypress)
        self.text.pack(side=tk.LEFT, expand=True, fill="both")
        self.scrbar = tk.Scrollbar(self)
        self.scrbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.scrbar.config(command=self.scroll)
        self.row = 0
        self.last_poll_row = -1
        self.auto_scroll = tk.IntVar()
        self.auto_scroll.set(1)
        self.idfmt = tk.IntVar()
        self.idfmt.set(canmsg.FORMAT_STD)
        self.saved_at_row = None
        self.create_menu()
        self.poll()
        self.scrollbar_update()

    def filter(self, canid):
        pass

    def wheel_up(self, event):
        self.scroll('scroll', '-5', 'units')

    def wheel_down(self, event):
        self.scroll('scroll', '5', 'units')

    def handle_configure(self, event):
        self.no_of_lines = event.height / self.line_height

    def create_menu(self):
        self.popup_menu = tk.Menu(self, tearoff=0)
        self.popup_menu.add_checkbutton(label='autoscroll'
                , variable=self.auto_scroll)

    def do_popup_menu(self, event):
        self.popup_menu.post(event.x_root - 5, event.y_root)

    def save(self, filename):
        self.log('Save: ' + filename)
        self.saved_at_row = self.row

    def poll(self):
        self.count = len(self.messages)
        if self.auto_scroll.get():
            self.row = self.count - self.no_of_lines
            if self.row < 0:
                self.row = 0
        if (self.row != self.last_poll_row) or (self.count < self.no_of_lines):
            self.last_poll_row = self.row
            self.text.delete('1.0', tk.END)
            start = self.row
            for i, m in enumerate(self.messages[start:start+self.no_of_lines]):
                s = self.fmt.format(str(m), start + i)
                self.text.insert(tk.END, s)
        self.after(50, self.poll)

    def handle_keypress(self, e):
        if e.keysym == 'End':
            self.scroll('moveto', '1.0')
        elif e.keysym == 'Home':
            self.scroll('moveto', '0.0')
        elif e.keysym == 'Prior':
            self.scroll('scroll', '-1', 'pages')
        elif e.keysym == 'Next':
            self.scroll('scroll', '1', 'pages')
        elif e.keysym == 'Up':
            self.scroll('scroll', '-1', 'units')
        elif e.keysym == 'Down':
            self.scroll('scroll', '1', 'units')
        else:
            return
        return 'break'

    def scroll(self, *args):
        if args[0] == 'scroll':
            d = int(args[1])
            if args[2] == 'pages':
                self.row += d * self.no_of_lines
            else:
                self.row += d
        elif args[0] == 'moveto':
            self.row = int(float(args[1]) * self.count)
        if self.row < 0:
            self.row = 0
        elif self.row > self.count:
            self.row = self.count
        self.scrollbar_update()

    def scrollbar_update(self):
        if self.count <= self.no_of_lines:
            a = 0.0
            b = 1.0
        else:
            a = 1.0 * self.row / self.count
            b = a + float(self.no_of_lines) / float(self.count)
        self.scrbar.set(a, b)
        self.after(100, self.scrollbar_update)

    def log(self, m):
        self.messages.append(m)

class LoggerWindow(tk.Toplevel):
    def __init__(self, channel):
        tk.Toplevel.__init__(self)
        self.channel = channel
        self.logger = Logger(self)
        self.logger.pack(expand=True, fill="both")
        self.bind('<KeyPress>', self.logger.handle_keypress)
        self.driver = canchannel.CanChannel(logger=self.logger)
        self.create_menu()
        self.poll()

#    def channel_setup(self):
#        ct = channel_types
#        for d in ct:
#            name = d.__name__
#            try:
#                self.driver = d(channel=self.channel, logger=self.logger)
#                break
#            except Exception as e:
#                fmt = 'Failed starting driver: {}: {}'
#                s = fmt.format(name, str(e)) 
#                self.logger.log(s)
#        fmt = 'Using driver: {}'
#        s = fmt.format(self.driver.__class__.__name__)
#        self.logger.log(s)

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
                , variable=self.logger.idfmt
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
        canmsg.format_set(self.logger.idfmt.get())
        
    def do_quit(self, *args):
        self.driver.close()
        self.quit()

    def poll(self):
        m = self.driver.read()
        while m:
            self.logger.log(m)
            m = self.driver.read()
        self.after(10, self.poll)

class PyCan(tk.Tk):
    def __init__(self, channel=0):
        tk.Tk.__init__(self)
        self.title('PyCAN')
        self.driver_frame = ttk.Frame(self)
        self.driver_frame.pack()
        self.driver_list = ttk.Treeview(self.driver_frame#, columns=['chno']
                , selectmode='browse')
        self.driver_list.heading('#0', text='Driver')
        #self.driver_list.heading('chno', text='Channel')
        self.driver_list.pack()
        for d, cs in channel_types:
            n = d.__name__
            iid = self.driver_list.insert('', index='end', text=n)
            for c in cs:
                self.driver_list.insert(iid, index='end', text=str(c))
        self.lw = LoggerWindow(channel)

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

