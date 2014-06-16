#!/usr/bin/env python
import sys
import pygtk
from gi.repository import Gtk, GLib, Gio, Gdk 
from gi.repository import AppIndicator3
import pycurl
from StringIO import StringIO
import xml.etree.ElementTree as ET
import webbrowser

# PING_FREQUENCY = 10
selectedPipelines = []
pathToIcon = "/home/kumaran/go-logo1.jpg"
urlOfXml = "http://sivakumaran-hp:8153/go/cctray.xml"
allData = []
selectedPipelines = []
stageDict = {}
jobDict = {}

class CheckGo:
    def __init__(self):
        self.ind = AppIndicator3.Indicator.new('go-indicator', '', AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
        self.ind.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.ind.set_icon(pathToIcon)
        self.ind.set_attention_icon("new-messages-red")

    def main(self):
        self.go_checker()
        # gtk.timeout_add(PING_FREQUENCY * 1000, self.go_checker)
        Gtk.main()
        #default refresh
        GLib.timeout_add_seconds(10, True)

    def go_checker(self):
        try:
            response_buffer = StringIO()
            curl = pycurl.Curl()
            curl.setopt(curl.URL, urlOfXml)
            curl.setopt(curl.WRITEFUNCTION, response_buffer.write)
            curl.perform()
            curl.close()
            xmlDoc = response_buffer.getvalue()
            data = []
            del allData[:]
            stageDict.clear()
            try:
                strXmlDoc = ET.fromstring(xmlDoc)
                for project in strXmlDoc.getiterator('Project'):
                    allData.append(str(project.attrib["name"]).split(" ")[0])

                for project in strXmlDoc.getiterator('Project'):
                    if(str(project.attrib["name"]).split(" ")[0] in selectedPipelines):
                        projectName = str(project.attrib["name"]).split(" ")[0]
                        data.append((projectName, project.attrib["activity"], project.attrib["lastBuildStatus"]))
                        
                        # print "job"
                        # print str(project.attrib["name"]).split(" :: ")[2]

                        try:
                            stageDict[projectName].append(str(project.attrib["name"]).split(" :: ")[1])
                        except:
                            stageDict[projectName] = []
                            stageDict[projectName].append(str(project.attrib["name"]).split(" :: ")[1])

                print stageDict
                print list(set(data))
                self.menu_setup(list(set(data)), stageDict)
            except:
                print "Error in parsing xml"
        except:
            print "Error in extracting xml from API"

    def menu_setup(self, data, stageDict):
        self.menu = Gtk.Menu()
        for project in data:
            if project[1] == "Sleeping":
                if project[2] == "Success":
                    status = "Success"
                    img = Gtk.Image.new_from_icon_name("gtk-ok", Gtk.IconSize.MENU)
                else:
                    status = "Failure"
                    img = Gtk.Image.new_from_icon_name("gtk-stop", Gtk.IconSize.MENU)
            else:
                status = "Building"
                img = Gtk.Image.new_from_icon_name("gtk-dialog-question", Gtk.IconSize.MENU)

            self.mitem = Gtk.ImageMenuItem.new_with_label(project[0])
            self.mitem.set_always_show_image(True)
            self.mitem.set_image(img)

            self.listMenu = Gtk.Menu()

            for x in set(stageDict[project[0]]):
                self.activityItem = Gtk.MenuItem(x)
                # self.activityItem.connect("activate", self.openUrl, project[3])
                self.activityItem.show()
                self.listMenu.append(self.activityItem)

            self.mitem.set_submenu(self.listMenu)
            self.mitem.show()
            self.menu.append(self.mitem)
            
        self.preferenceItem = Gtk.MenuItem("Preference")
        self.preferenceItem.connect("activate", self.preference)
        self.preferenceItem.show()
        self.menu.append(self.preferenceItem)

        self.refreshItem = Gtk.MenuItem("Refresh")
        self.refreshItem.connect("activate", self.refresh)
        self.refreshItem.show()
        self.menu.append(self.refreshItem)

        self.quit_item = Gtk.MenuItem("Quit")
        self.quit_item.connect("activate", self.quit)
        self.quit_item.show()
        self.menu.append(self.quit_item)
        
        self.ind.set_menu(self.menu)

    def quit(self, widget):
        sys.exit(0)

    def openUrl(self, widget, url):
        new = 2 # open in a new tab, if possible
        webbrowser.open(url, new = new)

    def refresh(self, widget):
        self.go_checker()

    def preference(self, widget):     
        window = Gtk.Window()
        window.set_title("Select Pipelines")
        window.set_border_width(80)
        vbox = Gtk.VBox(True, 2)
        window.add(vbox)
        button = Gtk.Button("Quit")
        button.connect("clicked", self.delete_event,window)
        vbox.pack_start(button, True, True, 2)
        button.show()
        vbox.show()
        print list(set(allData))
        for project in list(set(allData)):
            button = Gtk.CheckButton(project)
            button.connect("toggled", self.updateSelectedPipelines, project)
            vbox.pack_start(button, True, True, 2)
            button.show()
        window.show()

    def updateSelectedPipelines(self, button, name):
        if button.get_active():
            state = "on"
            selectedPipelines.append(name)
        else:
            state = "off"
            selectedPipelines.remove(name)

        print "selected Pipelines", selectedPipelines

    def delete_event(self, button, window):
        window.close()
        self.go_checker()

if __name__ == "__main__":
    indicator = CheckGo()
    indicator.main()