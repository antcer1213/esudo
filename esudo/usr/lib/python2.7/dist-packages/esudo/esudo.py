#!/usr/bin/python
# encoding: utf-8

"""eSudo - a GUI sudo tool in python and elementary

Base code by AntCer, polished by Jeff Hoogland
Something actually useful done by Kai Huuhko <kai.huuhko@gmail.com>
"""

import os
import getpass
import PAM
import ecore
import evas
import elementary
import argparse

_ = str

#----Popups
def pw_error_popup(en):
    win = en.top_widget_get()
    popup = elementary.Popup(win)
    popup.size_hint_weight = evas.EVAS_HINT_EXPAND, evas.EVAS_HINT_EXPAND
    popup.part_text_set("title,text", "Error")
    popup.text = "Incorrect Password!<br>Please try again."
    print("eSudo Error: Incorrect Password. Please try again.")
    popup.timeout = 3.0
    popup.show()

#----eSudo
class eSudo(object):
    def __init__( self, command=None, win=None, start_callback=None, end_callback=None, *args, **kwargs ):
        if not win:
            nowindow = True
            win = self.win = elementary.Window("esudo", elementary.ELM_WIN_DIALOG_BASIC)
            win.title = "eSudo"
            win.borderless = True
            win.size_hint_weight = evas.EVAS_HINT_EXPAND, evas.EVAS_HINT_EXPAND
            win.size_hint_align = evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL
            win.resize(300, 200)
            win.callback_delete_request_add(lambda o: elementary.exit())
            win.layer_set(11)
            #~ win.fullscreen = True
            win.show()
            win.activate()

            bg = elementary.Background(win)
            bg.size_hint_weight = 1.0, 1.0
            win.resize_object_add(bg)
            bg.show()

            self.embedded = False
        else:
            nowindow = False
            self.embedded = True

        self.cmd = command
        self.start_cb = start_callback if callable(start_callback) else None
        self.end_cb = end_callback if callable(end_callback) else None
        self.args = args
        self.kwargs = kwargs

#--------eSudo Window
        bz = elementary.Box(win)
        if nowindow:
            bz.size_hint_weight = evas.EVAS_HINT_EXPAND, 0.0
        else:
            bz.size_hint_weight = evas.EVAS_HINT_EXPAND, evas.EVAS_HINT_EXPAND
        bz.size_hint_align = evas.EVAS_HINT_FILL, 0.0
        bz.show()

        if nowindow:
            lbl = elementary.Label(win)
            lbl.style = "marker"
            lbl.color = 170, 170, 170, 255
            lbl.size_hint_align = 0.5, 0.0
            lbl.scale = 2.0
            lbl.text = "<b>eSudo</b>"
            bz.pack_end(lbl)
            lbl.show()

            sep = elementary.Separator(win)
            sep.horizontal = True
            bz.pack_end(sep)
            sep.show()

        if self.args:
            en = elementary.Entry(win)
            en.line_wrap_set(2)
            en.size_hint_align_set(-1.0, -1.0)
            en.size_hint_weight_set(0.0, 0.0)
            en.editable_set(False)
            #~ en.scrollable_set(True)
            en.entry_set("<b>Enter your password to perform<br>administrative tasks.</b><ps><ps>The application '%s' lets you modify<br>essential parts of your system."%self.cmd)
            bz.pack_end(en)
            en.show()
        else:
            fr = elementary.Frame(win)
            fr.text = "Command:"
            fr.size_hint_align = evas.EVAS_HINT_FILL, 0.0
            bz.pack_end(fr)
            fr.show()

            if nowindow:
                sep = elementary.Separator(win)
                sep.horizontal = True
                bz.pack_end(sep)
                sep.show()

            self.cmdline = cmdline = elementary.Entry(win)
            cmdline.elm_event_callback_add(self.entry_event)
            cmdline.single_line = True
            if self.cmd:
                cmdline.text = self.cmd
                cmdline.editable = False
            fr.content = cmdline
            cmdline.show()

        if nowindow:
            fr = elementary.Frame(win)
            fr.text = "Password:"
            fr.size_hint_align = evas.EVAS_HINT_FILL, 0.0
            bz.pack_end(fr)
            fr.show()
        else:
            bz1 = elementary.Box(win)
            bz.pack_end(bz1)
            bz1.show()

            lb = elementary.Label(win)
            lb.text = "<b>Password:</b>"
            lb.size_hint_align = 0.0, 0.5
            bz1.pack_end(lb)
            lb.show()

        en = self.en = elementary.Entry(win)
        en.name = "password"
        en.elm_event_callback_add(self.entry_event)
        en.single_line = True
        en.password = True
        en.show()

        if nowindow:
            fr.content = en
        else:
            bz1.pack_end(en)

        sep = elementary.Separator(win)
        sep.horizontal = True
        bz.pack_end(sep)
        sep.show()

        btnb = elementary.Box(win)
        btnb.horizontal = True
        btnb.size_hint_weight = evas.EVAS_HINT_EXPAND, 0.0
        btnb.size_hint_align = evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL
        bz.pack_end(btnb)
        btnb.show()

        bt = elementary.Button(win)
        bt.text = "Cancel"
        bt.callback_clicked_add(self.esudo_cancel, en)
        bt.size_hint_align = evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL
        bt.size_hint_weight = evas.EVAS_HINT_EXPAND, 0.0
        btnb.pack_end(bt)
        bt.show()

        bt = elementary.Button(win)
        bt.text = "OK"
        bt.callback_clicked_add(self.password_check, en)
        bt.size_hint_align = evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL
        bt.size_hint_weight = evas.EVAS_HINT_EXPAND, 0.0
        btnb.pack_end(bt)
        bt.show()

        self.iw = iw = elementary.InnerWindow(win)
        iw.content = bz
        iw.show()
        iw.activate()
        if self.cmd:
            en.focus = True

    def entry_event(self, obj, entry, event_type, event, *args):
        if event_type == evas.EVAS_CALLBACK_KEY_UP:
            if event.keyname == "Return":
                if entry.name == "password":
                    self.password_check(None, entry)
                else:
                    self.en.focus = True
            elif event.keyname == "Escape":
                self.close()

        return True

#--------Password Checker
    def password_check(self, bt, en):
        if not en.entry or not self.cmdline.entry:
            return

#------------Sets Password
        def pam_conv(auth, query_list, userData):
            password = en.entry
            resp = []
            for i in range(len(query_list)):
                query, type = query_list[i]
                if type == PAM.PAM_PROMPT_ECHO_ON or type == PAM.PAM_PROMPT_ECHO_OFF:
                    val = password
                    resp.append((val, 0))
                elif type == PAM.PAM_PROMPT_ERROR_MSG or type == PAM.PAM_PROMPT_TEXT_INFO:
                    resp.append(('', 0))
                else:
                    return None
            return resp

#------------Username & Service To Use
        username = getpass.getuser()

        with open("/etc/esudo/service") as file:
            service = file.readline()[:-1]

#------------Start Password Test
        auth = PAM.pam()
        auth.start(service)
        auth.set_item(PAM.PAM_USER, username)
        auth.set_item(PAM.PAM_CONV, pam_conv)
        try:
            auth.authenticate()
            auth.acct_mgmt()
        except PAM.error, resp:
            pw_error_popup(en)
            en.entry = ""
            en.focus = True
            return
        except:
            print("Internal error! File bug report.")
        else:
            self.esudo_ok(bt, en)

#--------eSudo Cancel Button
    def esudo_cancel(self, bt, en):
        en.entry = ""
        self.close()

    def close(self):
        self.iw.delete() if self.embedded else elementary.exit()

#--------eSudo OK Button
    def esudo_ok(self, bt, en):
        password = en.entry
        cmd = self.cmdline.entry
        cmdprts = cmd.split(" ")
        cmdnum = len(cmdprts)

        if self.args:
            cmd = "%s %s"%(cmd, ' '.join(self.args[0]))

        print("Starting '%s'..."%cmd)

        if cmdnum > 1:
            command = cmdprts[0]
            for i in range(cmdnum):
                if i > 0:
                    path = " ".join(cmdprts[i:])
                    if os.path.exists(path):
                        cmd = "%s '%s'"%(command, path)
                        break

        try:
            arguments = self.kwargs["cmdargs"]
            cmd = "%s %s"%(cmd, arguments)
        except:
            pass

        if not os.path.exists("/tmp/libesudo"):
            os.makedirs("/tmp/libesudo")
        command  = "cp /home/%s/.Xauthority /tmp/libesudo"%getpass.getuser()
        ecore.Exe(command, ecore.ECORE_EXE_PIPE_READ|ecore.ECORE_EXE_PIPE_ERROR|ecore.ECORE_EXE_PIPE_WRITE)

        self.run_command("HOME='/tmp/libesudo' ; sudo -S %s" % (cmd), password)

#--------Run Command
    def run_command(self, command, password):
        self.cmd_exe = cmd = ecore.Exe(command, ecore.ECORE_EXE_PIPE_READ|ecore.ECORE_EXE_PIPE_ERROR|ecore.ECORE_EXE_PIPE_WRITE)
        cmd.on_add_event_add(self.command_started)
        cmd.on_data_event_add(self.received_data)
        cmd.on_error_event_add(self.received_error, password)
        cmd.on_del_event_add(self.command_done)

    def command_started(self, cmd, event, *args, **kwargs):
        print("Command started.\n")
        if self.start_cb:
            try:
                self.start_cb(self.win, *self.args, **self.kwargs)
            except:
                print("Exception while running start_cb")
        self.iw.hide() if self.embedded else self.win.hide()

    def received_data(self, cmd, event, *args, **kwargs):
        if not "\n" == event.data:
            print(event.data)

    def received_error(self, cmd, event, *args, **kwargs):
        if not "sudo" in event.data or not "password for" in event.data:
            print("Error: %s"%event.data)
        else:
            password = args[0]
            cmd.send(str(password)+"\n")

    def command_done(self, cmd, event, *args, **kwargs):
        print("Command done.")

        if self.end_cb:
            try:
                self.end_cb(event.exit_code, self.win, *self.args, **self.kwargs)
            except:
                print("Exception while running end_cb")
        self.close()

if __name__ == "__main__":
    import sys

    parser = argparse.ArgumentParser(prog='esudo', description=_('A GUI sudo tool in python and elementary'))
    parser.add_argument('command', nargs='?', help=_('Command to run with elevated privileges.'))
    parser.add_argument('argument', nargs=argparse.REMAINDER, help=_('Arguments of command to run.'))
    clargs = vars(parser.parse_args())

    cmd = " ".join(sys.argv[1:])

    elementary.init()

    start = eSudo(cmd)

    elementary.run()
    elementary.shutdown()
