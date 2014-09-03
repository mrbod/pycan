''' Python CAN bus monitor

Splendid indeed'''

import sys
if sys.version_info.major > 2:
    import tkinter as tk
    import tkinter.ttk as ttk
    import tkinter.messagebox as messagebox
    import tkinter.filedialog as tkFileDialog
    import tkinter.colorchooser as tkColorChooser
    import tkinter.font as tkFont
else:
    import Tkinter as tk
    import ttk
    import tkMessageBox as messagebox
    import tkFileDialog
    import tkColorChooser
    import tkFont
import os
import re

from pycan import dialog
from pycan import canchannel
from pycan import kvaser
from pycan import canmsg

class IDMaskDialog(tk.Toplevel):
    '''Dialog for setting of ID and MASK'''
    def __init__(self, master, *args, **kwargs):
        title = kwargs.pop('title', '')
        tk.Toplevel.__init__(self, master=master, *args, **kwargs)
        self.title('Mask/ID')
        self.result = None
        self.mask = ''
        self.can_id = ''
        self.transient(master)
        l = ttk.Label(self, text=title)
        l.pack()
        input_box_frame = ttk.Frame(self)
        ttk.Label(input_box_frame, text='Mask').grid(row=0, column=0)
        ttk.Label(input_box_frame, text='ID').grid(row=1, column=0)
        self.emask = ttk.Entry(input_box_frame)
        self.emask.grid(row=0, column=1)
        self.eid = ttk.Entry(input_box_frame)
        self.eid.grid(row=1, column=1)
        input_box_frame.pack(padx=5, pady=5)
        button_frame = ttk.Frame(self)
        button = ttk.Button(button_frame, text='OK', command=self.ok)
        button.pack(side=tk.LEFT, padx=5, pady=5)
        button = ttk.Button(button_frame, text='Cancel', command=self.cancel)
        button.pack(side=tk.LEFT, padx=5, pady=5)
        button_frame.pack()

    def ok(self, *args):
        self.mask = int(self.emask.get(), 0)
        self.can_id = int(self.eid.get(), 0)
        self.result = True
        self.destroy()

    def cancel(self, *args):
        self.destroy()

class Logger(ttk.Frame):
    def __init__(self, master=None):
        ttk.Frame.__init__(self, master=master)
        self.messages = []
        self.count = len(self.messages)
        if os.name == 'nt':
            self.font = tkFont.Font(family='Courier')
        else:
            self.font = tkFont.Font(family='monospace')
        self.line_height = int(self.font.metrics('linespace'))
        self.no_of_lines = 0
        self.text = tk.Text(self, font=self.font)
        self.bind('<Configure>', self.handle_configure)
        # mouse buttons
        self.text.bind('<Button-1>', lambda x: None)
        self.text.bind('<Button-2>', lambda x: None)
        self.text.bind('<Button-3>', self.do_popup_menu)
        # scroll wheel on windows
        self.text.bind('<MouseWheel>', self.mouse_wheel)
        # scroll wheel on linux
        self.text.bind('<Button-4>', self.mouse_wheel)
        self.text.bind('<Button-5>', self.mouse_wheel)
        # key presses
        self.text.bind('<KeyPress>', self.handle_keypress)
        self.text.pack(side=tk.LEFT, expand=True, fill="both")
        self.scrbar = tk.Scrollbar(self)
        self.scrbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.scrbar.config(command=self.scroll)
        self.row = 0
        self.last_poll_row = -1
        self.auto_scroll = tk.IntVar()
        self.auto_scroll.set(1)
        self.time_format = tk.IntVar()
        self.time_format.set(0)
        self.idfmt = tk.IntVar()
        self.idfmt.set(canmsg.FORMAT_STD)
        self.fmt = ''
        self.id_format()
        self.saved_at_row = None
        self.color_codes = []
        self.create_menu()
        self.poll()
        self.scrollbar_update()
        self._filter = lambda x: x

    def id_format(self):
        '''Set CAN message format'''
        self.fmt = '{1:5d}: ' + canmsg.formats[self.idfmt.get()] + '\n'

    def filter(self, msg):
        '''Run CAN message through filter'''
        return self._filter(msg)

    def color_code(self, msg):
        '''Apply color code'''
        for i, mask, color_code in self.color_codes:
            if (msg.can_id ^ i) & mask == 0:
                return color_code
        return None

    def mouse_wheel(self, event):
        '''Handle scroll wheel'''
        if event.num == 4 or event.delta == 120:
            self.scroll('scroll', '-5', 'units')
        elif event.num == 5 or event.delta == -120:
            self.scroll('scroll', '5', 'units')

    def handle_configure(self, event):
        '''Handle configure'''
        self.no_of_lines = event.height // self.line_height

    def filter_mask_id(self):
        try:
            dlg = IDMaskDialog(self, title='Filter mask/id')
        except Exception as e:
            print(str(e))
        self.wait_window(dlg)
        if dlg.result:
            def filt(msg):
                '''New filter function'''
                if (msg.can_id ^ dlg.can_id) & dlg.mask > 0:
                    return None
                return msg
            self._filter = filt

    def filter_bican(self):
        pass

    def filter_free_form(self):
        pass

    def color_mask_id(self):
        '''Set color code MASK and ID'''
        dlg = IDMaskDialog(self, title='Color mask/id')
        self.wait_window(dlg)
        if dlg.result:
            color = tkColorChooser.askcolor(parent=self)[1]
            self.color_codes.append((dlg.can_id, dlg.mask, color))
            self.text.tag_config(color, background=color)

    def create_menu(self):
        '''Create menu'''
        self.popup_menu = tk.Menu(self, tearoff=0)
        self.popup_menu.add_checkbutton(label='relative time', underline=0
                , variable=self.time_format)
        self.popup_menu.add_checkbutton(label='autoscroll', underline=0
                , variable=self.auto_scroll)
        self.popup_menu.add_checkbutton(label='bican format', underline=0
                , variable=self.idfmt
                , onvalue=canmsg.FORMAT_BICAN, offvalue=canmsg.FORMAT_STD
                , command=self.id_format)
        self.id_format_menu = tk.Menu(self, tearoff=0)
        self.popup_menu.add_cascade(menu=self.id_format_menu, label='id number format')
        self.id_format_value = tk.IntVar()
        self.id_format_value.set(2)
        self.id_format_menu.add_radiobutton(label='bin', value=0
                , variable=self.id_format_value)
        self.id_format_menu.add_radiobutton(label='dec', value=1
                , variable=self.id_format_value)
        self.id_format_menu.add_radiobutton(label='hex', value=2
                , variable=self.id_format_value)
        self.filter_menu = tk.Menu(self, tearoff=0)
        self.popup_menu.add_cascade(menu=self.filter_menu, label='filter')
        self.filter_menu.add_command(label='mask/id', underline=0
                , command=self.filter_mask_id)
        #self.filter_menu.add_command(label='bican', underline=0
        #        , command=self.filter_bican)
        #self.filter_menu.add_command(label='free form', underline=0
        #        , command=self.filter_free_form)
        self.color_menu = tk.Menu(self, tearoff=0)
        self.color_menu.add_command(label='mask/id', underline=0
                , command=self.color_mask_id)
        self.popup_menu.add_cascade(menu=self.color_menu, label='color code')

    def do_popup_menu(self, event):
        '''Handle popup menu event'''
        self.popup_menu.post(event.x_root - 10, event.y_root)

    def save(self, filename):
        '''Save windows contents'''
        try:
            with open(filename, 'w') as output_file:
                for i, msg in enumerate(self.messages):
                    line = self.fmt.format(msg, i)
                    output_file.write(line)
                    self.saved_at_row = i
        except Exception as e:
            messagebox.showerror('File save error', str(e))

    def poll(self):
        '''Do stuff at poll intervall'''
        self.count = len(self.messages)
        if self.auto_scroll.get():
            self.row = self.count - self.no_of_lines
            if self.row < 0:
                self.row = 0
        redraw = ((self.row != self.last_poll_row)
                or (self.count < self.no_of_lines)
                or ((self.row + self.no_of_lines > self.count)))
        if redraw:
            self.last_poll_row = self.row
            self.text.delete('1.0', tk.END)
            start = self.row
            end = start + self.no_of_lines
            msgs = self.messages[start:end]
            for i, msg in enumerate(msgs):
                if isinstance(msg, str):
                    line = msg[0:]
                else:
                    line = self.fmt.format(msg, start + i)
                color_code = self.color_code(msg)
                if color_code:
                    self.text.insert(tk.END, line, (color_code,))
                else:
                    self.text.insert(tk.END, line)
        self.after(50, self.poll)

    def handle_keypress(self, event):
        '''Handle keyboard input'''
        if event.keysym == 'End':
            percentage = float(self.count - self.no_of_lines + 1) // self.count
            self.scroll('moveto', str(percentage))
        elif event.keysym == 'Home':
            self.scroll('moveto', '0.0')
        elif event.keysym == 'Prior':
            self.scroll('scroll', '-1', 'pages')
        elif event.keysym == 'Next':
            self.scroll('scroll', '1', 'pages')
        elif event.keysym == 'Up':
            self.scroll('scroll', '-1', 'units')
        elif event.keysym == 'Down':
            self.scroll('scroll', '1', 'units')
        else:
            return
        return 'break'

    def scroll(self, *args):
        '''Handle scrolling'''
        if args[0] == 'scroll':
            amount = int(args[1])
            if args[2] == 'pages':
                self.row += amount * self.no_of_lines
            else:
                self.row += amount
        elif args[0] == 'moveto':
            self.row = int(float(args[1]) * self.count)
        if self.row < 0:
            self.row = 0
        elif self.row > (self.count - self.no_of_lines):
            self.row = self.count - self.no_of_lines
        self.scrollbar_update()

    def scrollbar_update(self):
        '''Update scollbar'''
        if self.count <= self.no_of_lines:
            start = 0.0
            end = 1.0
        else:
            start = 1.0 * self.row // self.count
            end = start + float(self.no_of_lines) // float(self.count)
        self.scrbar.set(start, end)
        self.after(100, self.scrollbar_update)

    def log(self, msg):
        '''Handle the logging of messages'''
        if self.filter(msg):
            self.messages.append(msg)

class LoggerWindow(tk.Toplevel):
    '''A logging window'''
    def __init__(self, driver, channel, bitrate):
        tk.Toplevel.__init__(self)
        self.logger = Logger(self)
        self.logger.pack(expand=True, fill="both")
        self.bind('<KeyPress>', self.logger.handle_keypress)
        try:
            self.driver = driver(logger=self.logger, channel=channel, bitrate=bitrate)
        except:
            self.destroy()
            raise
        self.create_menu()
        self.poll()

    def create_menu(self):
        '''Menu creation'''
        menu = tk.Menu(self)
        self.config(menu=menu)
        filemenu = tk.Menu(menu, tearoff=0)
        filemenu.add_command(label='Save', underline=0,
                accelerator='C-s', command=self.do_save)
        self.bind_all('<Control-Key-s>', self.do_save)
        filemenu.add_command(label='Exit', underline=1,
                accelerator='C-q', command=self.do_quit)
        menu.add_cascade(label='File', underline=0, menu=filemenu)
        menu.add_cascade(label='Logger', underline=0
                , menu=self.logger.popup_menu)
        actionmenu = tk.Menu(menu)
        actionmenu.add_command(label='Send', command=self.do_send)
        menu.add_cascade(label='Action', underline=0, menu=actionmenu)

    def do_save(self, *args):
        '''Save file handling'''
        filename = tkFileDialog.asksaveasfilename(initialdir=os.getcwd())
        self.logger.save(filename)

    def do_send(self):
        '''Send a message'''
        msg = canmsg.CanMsg()
        msg.extended = False
        msg.addr = 0
        msg.group = canmsg.GROUP_POUT
        msg.type = canmsg.TYPE_MON
        msg.data = [ord(c) for c in 'abcdef']
        self.driver.write(msg)

    def do_quit(self, *args):
        '''Handle quit'''
        self.driver.close()
        self.quit()

    def poll(self):
        '''Poll for messages'''
        msg = self.driver.read()
        while msg:
            msg = self.driver.read()
        self.after(10, self.poll)

def channel_setup():
    '''Channel setup'''
    channel_types = {}
    channel_types['Simulated'] = (canchannel.CanChannel, ('Internal',), None)
    kvaser_channels = kvaser.list_channels()
    if len(kvaser_channels) > 0:
        br = kvaser.bitrates
        channel_types['Kvaser'] = (kvaser.KvaserCanChannel, kvaser_channels, br)
    return channel_types

class BaudSelector(dialog.Dialog):
    def __init__(self, parent, baudrates):
        self.br = baudrates
        super(BaudSelector, self).__init__(parent, title='Select bitrate')

    def body(self, master):
        self.selection = tk.StringVar()
        self.selection.set('125')
        x = self.br
        x = x.items()
        x = [(k, v[0]) for k, v in x]
        x.sort(key=lambda z: z[1])
        self.x = [a[0] for a in x]
        self.combo = ttk.Combobox(master, textvariable=self.selection, values=self.x)
        self.combo.state(['!disabled', 'readonly'])
        self.combo.pack()
        return self.combo

    def run(self):
        super(BaudSelector, self).run()
        return self.selection.get()

class PyCan(tk.Tk):
    '''This is the class'''
    def __init__(self):
        tk.Tk.__init__(self)
        self.center()
        self.title('PyCAN')
        self.bind_all('<Control-Key-q>', self.do_quit)
        self.driver_frame = ttk.Frame(self)
        self.driver_frame.pack(fill=tk.BOTH)
        self.driver_list = ttk.Treeview(self.driver_frame
                , selectmode='browse')
        self.driver_list.heading('#0', text='Driver')
        self.driver_list.pack(fill=tk.BOTH)
        channels = channel_setup()
        keys = list(channels.keys())
        keys.sort()
        for k in keys:
            chns = channels[k][1]
            br = channels[k][2]
            self.driver_list.insert('', index='end', text=k, iid=k)
            for i, clsname in enumerate(chns):
                ciid = '{}_{}'.format(k, i)
                self.driver_list.insert(k, index='end', text=clsname, iid=ciid
                        , tags='channel')
        self.driver_list.tag_bind('channel', '<<TreeviewOpen>>', self.do_open)
        self.driver_list.tag_bind('channel', '<<TreeviewClose>>', self.do_open)

    def center(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry('{0}x{1}+{2}+{3}'.format(width, height, x, y))

    def do_open(self, *args):
        '''Open driver channel'''
        iid = self.driver_list.focus()
        parent = self.driver_list.parent(iid)
        pattern = parent + r'_(\d+)'
        channel = int(re.match(pattern, iid).group(1))
        try:
            channel_types = channel_setup()
            driver_cls = channel_types[parent][0]
            baudrates = channel_types[parent][2]
            br = None
            if baudrates:
                bs = BaudSelector(self, baudrates)
                br = bs.run()
            LoggerWindow(driver_cls, channel, br)
        except Exception as e:
            title = 'Failed to open {} {}'.format(parent, channel)
            messagebox.showerror(title, str(e))

    def do_quit(self, *args):
        '''Quit'''
        self.quit()

def main():
    '''Main'''
    try:
        app = PyCan()
        app.mainloop()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        messagebox.showerror('Exception', str(e))

