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
pathToIcon = "/home/kumaran/Indix/go-indicator/go-logo.jpg"
urlOfXml = "http://sivakumaran-hp:8153/go/cctray.xml"
# pathToIcon = "/media/yooo/5A3426C44A1D9AD2/Indix/Hackn8/MyGoPanel/go.png"
# urlOfXml = "http://abyss:8153/go/cctray.xml"
stageDict = {}
username = ''
password = ''

class Job:

    name = ""
    lastBuildStatus = ""
    activity = ""
    url = ""

    def __init__(self, name, lastBuildStatus, activity, url):
        self.name = name
        self.lastBuildStatus = lastBuildStatus
        self.activity = activity
        self.url = url

class goIndicator:

    def __init__(self):
        self.ind = AppIndicator3.Indicator.new('go-indicator', '', AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
        self.ind.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.ind.set_icon(pathToIcon)
        self.ind.set_attention_icon("new-messages-red")      #change the icon


    def getXmlResponse(self, username, password):            #username, password
        try:
            responseBuffer = StringIO()
            curl = pycurl.Curl()
            curl.setopt(curl.URL, urlOfXml)
            curl.setopt(curl.WRITEFUNCTION, responseBuffer.write)
            curl.perform()
            curl.close()
            return responseBuffer.getvalue()
        except:
            print "Error in getting the xml response"


    def main(self):
        xml = self.getXmlResponse(username, password)
        [projectDetails, projectNameList] = self.parseXml(xml)
        self.createMenu(projectDetails, projectNameList)
        # gtk.timeout_add(PING_FREQUENCY * 1000, self.go_checker)
        Gtk.main()
        #default refresh
        GLib.timeout_add_seconds(10, True)


    def parseXml(self, xml):
        projectDetails = {}
        projectNameList = []
        try:
            strXml = ET.fromstring(xml)
            for project in strXml.getiterator('Project'):
                pipenameParts = str(project.attrib["name"]).split(" :: ")
                projectName = pipenameParts[0]
                projectNameList.append(projectName)
                if pipenameParts[0] in selectedPipelines and len(pipenameParts) == 3:
                    stageName = pipenameParts[1]
                    jobName = pipenameParts[2]
                    activity = project.attrib['activity']
                    lastBuildStatus = project.attrib['lastBuildStatus']
                    url = project.attrib['webUrl']
                    jobObject = Job(jobName, activity, lastBuildStatus, url)
                    try:
                        projectDetails[projectName][stageName].append(jobObject)
                    except:
                        try:
                            projectDetails[projectName][stageName] = [jobObject]
                        except:
                            projectDetails[projectName] = {stageName : [jobObject]}
            projectNameList = list(set(projectNameList))          
            return [projectDetails, projectNameList]
        except:
            print "Error while parsing the xml"
                
        
    def getStatusImage(self, project):
        for stage in project.keys():
            for job in project[stage]:
                print job.lastBuildStatus , job.activity
                if 'Building' in job.lastBuildStatus:
                    return Gtk.Image.new_from_icon_name("gtk-dialog-question", Gtk.IconSize.MENU)
                elif 'Failure' in job.activity:
                    return Gtk.Image.new_from_icon_name("gtk-stop", Gtk.IconSize.MENU)
        return Gtk.Image.new_from_icon_name("gtk-ok", Gtk.IconSize.MENU)

    
    def createMenu(self, projectDetails, projectNameList):
        self.pipelineMenu = Gtk.Menu()
        print "details ", projectNameList, selectedPipelines
        try:
            for project in selectedPipelines:
                self.pipelineItem = Gtk.ImageMenuItem.new_with_label(project)
                self.pipelineItem.set_always_show_image(True)
                self.stageMenu = Gtk.Menu()
                stagesInProject = projectDetails[project].keys()
                img = self.getStatusImage(projectDetails[project])
                for stage in stagesInProject:
                    self.stageItem = Gtk.MenuItem(stage)
                    self.jobMenu = Gtk.Menu()
                    for job in projectDetails[project][stage]:
                        self.jobItem = Gtk.MenuItem(job.name)
                        self.jobItem.connect("activate", self.openUrl, job.url)       
                        self.jobItem.show()
                        self.jobMenu.append(self.jobItem)             
                    self.jobMenu.show()
                    self.stageItem.set_submenu(self.jobMenu)
                    self.stageItem.show()
                    self.stageMenu.append(self.stageItem)
                self.stageMenu.show() 
                self.pipelineItem.set_submenu(self.stageMenu)
                self.pipelineItem.set_image(img)
                self.pipelineItem.show()
                self.pipelineMenu.append(self.pipelineItem)
        except:
            print "Error while creating menu"
        self.pipelineMenu.show()
       
        self.preferenceItem = Gtk.MenuItem("Preference")
        self.preferenceItem.connect("activate", self.preference, projectNameList)
        self.preferenceItem.show()
        self.pipelineMenu.append(self.preferenceItem)

        self.refreshItem = Gtk.MenuItem("Refresh")
        self.refreshItem.connect("activate", self.refresh)
        self.refreshItem.show()
        self.pipelineMenu.append(self.refreshItem)

        self.quit_item = Gtk.MenuItem("Quit")
        self.quit_item.connect("activate", self.quit)
        self.quit_item.show()
        self.pipelineMenu.append(self.quit_item)
        
        self.ind.set_menu(self.pipelineMenu)

    def quit(self, widget):
        sys.exit(0)

    def openUrl(self, widget, url):
        new = 2 # open in a new tab, if possible
        webbrowser.open(url, new = new)

    def refresh(self, widget):
        self.main()

    def preference(self, widget, projectNameList):
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
        for project in projectNameList:
            button = Gtk.CheckButton(project)
            button.connect("toggled", self.updateSelectedPipelines, project)
            vbox.pack_start(button, True, True, 2)
            if project in selectedPipelines:
                button.set_active(project)
            button.show()
        window.show()

    def updateSelectedPipelines(self, button, name):
        if button.get_active() and name not in selectedPipelines:
            state = "on"
            selectedPipelines.append(name)
        elif not button.get_active() and name in selectedPipelines:
            state = "off"
            selectedPipelines.remove(name)

        print "selected Pipelines", selectedPipelines

    def delete_event(self, button, window):
        window.close()
        self.main()

if __name__ == "__main__":
    indicator = goIndicator()
    indicator.main()