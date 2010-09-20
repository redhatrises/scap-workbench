#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010 Red Hat Inc., Durham, North Carolina.
# All Rights Reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Authors:
#      Maros Barabas        <mbarabas@redhat.com>
#      Vladimir Oberreiter  <xoberr01@stud.fit.vutbr.cz>

import pygtk
import gtk
import gobject
import pango

import abstract
import logging
import core
from events import EventObject

import commands
import render


class ScanList(abstract.List):
    
    def __init__(self, core=None, progress=None):
        self.core = core
        self.data_model = commands.DHScan(core, progress=progress)
        abstract.List.__init__(self, "gui:scan:scan_list", core)
        self.get_TreeView().set_enable_tree_lines(True)

        selection = self.get_TreeView().get_selection()
        selection.set_mode(gtk.SELECTION_SINGLE)

        # actions
        self.add_receiver("gui:btn:menu:scan", "scan", self.__scan)
        self.add_receiver("gui:btn:menu:scan", "cancel", self.__cancel)
        self.add_receiver("gui:btn:menu:scan", "export", self.__export)

    def __export(self):
        self.data_model.export()

    def __cancel(self):
        self.data_model.cancel()

    def __scan(self):
        self.data_model.scan()

class MenuButtonScan(abstract.MenuButton):
    """
    GUI for refines.
    """
    def __init__(self, box, widget, core):
        abstract.MenuButton.__init__(self, "gui:btn:menu:scan", widget, core)
        self.core = core
        self.box = box

        #draw body
        self.body = self.draw_body()

        # set signals
        self.add_sender(self.id, "scan")
        self.add_sender(self.id, "cancel")
        self.add_sender(self.id, "export")

    #callback function
    def cb_btnStart(self, widget):
        self.emit("scan")

    def cb_btnCancel(self, widget):
        self.emit("cancel")

    def cb_btnExpXccdf(self, widget):
        self.emit("export")

    def cb_btnHelp(self, widget):
        window = HelpWindow(self.core)

    #draw
    def draw_body(self):
        body = gtk.VBox()
        
        alig = gtk.Alignment(0.5, 0.5, 1, 1)
        alig.set_padding(10, 10, 10, 10)
        body.add(alig)
        
        vbox_main = gtk.VBox()
        alig.add(vbox_main)
        self.progress = gtk.ProgressBar()

        # Scan list
        self.scanList = ScanList(core=self.core, progress=self.progress)
        vbox_main.pack_start(self.scanList.get_widget(), True, True, 2)
        
        vbox_main.pack_start(gtk.HSeparator(), False, True, 2)
        
        #Progress Bar
        vbox_main.pack_start(self.progress, False, True, 2)
        
        #Buttons
        btnBox = gtk.HButtonBox()
        btnBox.set_layout(gtk.BUTTONBOX_START)
        vbox_main.pack_start(btnBox, False, True, 2)
        
        btn = gtk.Button("Scan")
        btn.connect("clicked", self.cb_btnStart)
        btnBox.add(btn)
        
        btn = gtk.Button("Stop")
        btn.connect("clicked", self.cb_btnCancel)
        btnBox.add(btn)
        
        btn = gtk.Button("Export results")
        btn.connect("clicked", self.cb_btnExpXccdf)
        btnBox.add(btn)
        
        btn = gtk.Button("Help")
        btn.connect("clicked", self.cb_btnHelp)
        btnBox.add(btn)

        body.show_all()
        body.hide()
        self.box.add(body)
        return body
        

class HelpWindow(abstract.Window):

    def __init__(self, core=None):
        self.core = core
        self.builder = gtk.Builder()
        self.builder.add_from_file("glade/scan_help.glade")
        self.draw_window()

    def delete_event(self, widget, event):
        self.window.destroy()
        
    def __notify(self, widget, event):
        if event.name == "width":
            for cell in widget.get_cell_renderers():
                cell.set_property('wrap-width', widget.get_width())

    def draw_window(self):
        # Create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window = self.builder.get_object("scan:help:window")
        self.treeView = self.builder.get_object("scan:help:treeview")
        self.help_model = self.builder.get_object("scan:help:treeview:model")
        self.builder.connect_signals(self)

        txtcell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Result", txtcell, text=0)
        column.add_attribute(txtcell, 'background', 1)
        self.treeView.append_column(column)

        txtcell = gtk.CellRendererText()
        txtcell.set_property('wrap-mode', pango.WRAP_WORD)
        txtcell.set_property('wrap-width', 500)
        column = gtk.TreeViewColumn("Description", txtcell, text=2)
        column.set_resizable(True)
        column.set_expand(True)
        column.connect("notify", self.__notify)
        self.treeView.append_column(column)

        selection = self.treeView.get_selection()
        selection.set_mode(gtk.SELECTION_NONE)

        self.help_model.append(["PASS", commands.DHScan.BG_GREEN, "The target system or system component satisfied all the conditions of the Rule. A pass result contributes to the weighted score and maximum possible score."])
        self.help_model.append(["FAIL", commands.DHScan.BG_RED, "The target system or system component did not satisfy all the conditions of the Rule. A fail result contributes to the maximum possible score."])
        self.help_model.append(["ERROR", commands.DHScan.BG_ERR, "The checking engine encountered a system error and could not complete the test, therefore the status of the target’s compliance with the Rule is not certain. This could happen, for example, if a Benchmark testing tool were run with insufficient privileges."])
        self.help_model.append(["UNKNOWN", commands.DHScan.BG_GRAY, "The testing tool encountered some problem and the result is unknown. For example, a result of ‘unknown’ might be given if the Benchmark testing tool were unable to interpret the output of the checking engine."])
        self.help_model.append(["NOT APPLICABLE", commands.DHScan.BG_GRAY, "The Rule was not applicable to the target of the test. For example, the Rule might have been specific to a different version of the target OS, or it might have been a test against a platform feature that was not installed. Results with this status do not contribute to the Benchmark score."])
        self.help_model.append(["NOT CHECKED", commands.DHScan.BG_GRAY, "The Rule was not evaluated by the checking engine. This status is designed for Rules that have no check properties. It may also correspond to a status returned by a checking engine. Results with this status do not contribute to the Benchmark score."])
        self.help_model.append(["NOT SELECTED", commands.DHScan.BG_GRAY, "The Rule was not selected in the Benchmark. Results with this status do not contribute to the Benchmark score."])
        self.help_model.append(["INFORMATIONAL", commands.DHScan.BG_LGREEN, "The Rule was checked, but the output from the checking engine is simply information for auditor or administrator; it is not a compliance category. This status value is designed for Rules whose main purpose is to extract information from the target rather than test compliance. Results with this status do not contribute to the Benchmark score."])
        self.help_model.append(["FIXED", commands.DHScan.BG_FIXED, "The Rule had failed, but was then fixed (possibly by a tool that can automatically apply remediation, or possibly by the human auditor). Results with this status should be scored the same as pass."])

        self.window.show_all()

    def destroy_window(self, widget):
        self.window.destroy()
