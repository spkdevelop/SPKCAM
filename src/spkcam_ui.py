#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2015 Daniel Fernandez (daniel@spkautomatizacion.com), Saul Pilatowsky (saul@spkautomatizacion.com) 
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# The user interface was created using Mark Meier UI Library.  
# http://mkmra2.blogspot.com/2012/12/creating-graphical-user-interfaces-with.html
# The file uploader (MultipartPostHangler.py) was created by Will Holcomb <wholcomb@gmail.com>
#
# Find us at: http://www.spkautomatizacion.com

import rhinoscriptsyntax as rs
import operator
import Rhino
import os
import shutil
import urllib2
import threading
import thread
import json
import System.Windows.Forms.DialogResult
from lib import Meier_UI_Utility
from lib import MultipartPostHandler
from lib import usermanager as um
import webbrowser
from lib.g_instances import g_curve
from lib.gcode_preview import vectors_from_gcode
from lib import lang_manager

#Revisa los folders de inatalción y si no hay local genera uno pera guardar las rutinas personalizadas.

def recursive_overwrite(src, dest, ignore=None):
    if os.path.isdir(src):
        if not os.path.isdir(dest):
            os.makedirs(dest)
        files = os.listdir(src)
        if ignore is not None:
            ignored = ignore(src, files)
        else:
            ignored = set()
        for f in files:
            if f not in ignored:
                recursive_overwrite(os.path.join(src, f), 
                                    os.path.join(dest, f), 
                                    ignore)
    else:
        shutil.copyfile(src, dest)
        
def check_language_and_conditions():
    f = open(os.path.join(os.path.split(SETTINGS_FILE)[0],"initial_settings.txt"),"r")
    r = f.read()
    f.close()
    init_settings = eval(r) 
    if not init_settings["terms"]:
        lang =  rs.MultiListBox(["Espanol","English"],"Idioma/Language:", "SPKCAM: %s"%VERSION)
        if not lang: return False
        set_lang = "es" if lang[0] == "Espanol" else "en"
        terms = "Bienvenido a SPK:.cam %s WIP\n\n%s\n\nhttps://www.spkautomatizacion.com/spkcam_terms_and_conditions" % (VERSION,lang_manager.get_ui_text(set_lang)["terms"])

        if rs.MessageBox(terms, 4 | 32) == 6:
            
            init_settings = {"terms":True,"lang":set_lang}
            f = open(os.path.join(os.path.split(SETTINGS_FILE)[0],"initial_settings.txt"),"w")
            r = f.write(str(init_settings))
            f.close()
        else:
            print "¡Cerrando inesperadamente!"
            return False
    return init_settings["lang"]

def get_working_path():
    real_path = os.path.dirname(os.path.realpath(__file__))
    if not "Rhino" in real_path: return real_path
    spkcam_id = Rhino.PlugIns.PlugIn.IdFromName("Spkcam")
    plugin = Rhino.PlugIns.PlugIn.Find(spkcam_id)
    appdata_path = os.path.split(plugin.Assembly.Location)[0]
    roaming_folder = os.getenv('APPDATA')
    local_install = True if roaming_folder in appdata_path else False
    if not local_install:
        local_path = os.path.join(roaming_folder,"\\".join(appdata_path.split("\\")[3:]))
        if not os.path.exists(local_path):
            recursive_overwrite(os.path.join(appdata_path,"res"), os.path.join(local_path,"res"))
        appdata_path = local_path
    return appdata_path

alias_name = "Spkcam"
script_password="3VERyuNQwfeJtzX"
base_url= "https://spkcloud.appspot.com/_cam/upload"
spk_page = "http://www.spkautomatizacion.com"
REGISTRY_SECTION = "Spkcam1.6b"
VERSION = "Versión lin-1.6b 2016"
IN_TEXT = ["(SPK:. Generador CodigoG %s)" % VERSION,"G21","G90","G54","M3"]
OUT_TEXT = ["(ending)","M5","G0X0Y0"]
PREVIEW_LAYER_NAME = "Spkcam preview"
OFFSET_LAYER = "Offset curves"
LAYER_SORTING = "Tags orden"
LAYER_CLUSTER = "Tags cluster"
TRASH_LAYER = "Trash"

appdata_path = get_working_path()
SETTINGS_FILE = os.path.join(appdata_path, "res","Settings","MachiningSettings.txt")
TEMP_GCODE_FILE = os.path.join(appdata_path, "res","Settings","Temp_gcode_file.txt")
IMAGE_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), "res","Icons","")
SNAPSHOT_FOLDER =  os.path.join(appdata_path, "res","Snapshots","")
if not os.path.exists(SNAPSHOT_FOLDER): os.makedirs(SNAPSHOT_FOLDER)
        
LANG = check_language_and_conditions()
VARIABLE_NAMES = lang_manager.get_variable_names()
INPUT_VALUES = lang_manager.get_input_values(LANG if LANG else "es")
CLUSTER_TOLERANCE = 1
TXT = lang_manager.get_ui_text(LANG)

class LoginThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.user_mail = False

    def run(self):

        self.user_mail = um.login()
        

class SettingsControl():
    
    def __init__(self,generalSettings,machiningSettings,userData):
        # Make a new form (dialog)
        self.rhino_objects = None 
        self.sorted_objects = None
        self.time = 0
        self.code_thread = False
        self.login_thread = False
        self.terminal_lines = ["","",""]
        self.spkmodel_objects = None
        self.general_settings = {"sec_plane":6,"feed_rapid":3000,"cut_diam":6} if not generalSettings else generalSettings
        self.machining_settings = {} if not machiningSettings else machiningSettings
        self.user_data = {"technical_name":False,"save_file":False,"spkcam_session_token":False,"material_info":False,"sort_closest":False,"user_data":False,"sorting":True,"name_url":False,"autocluster":True,"index_pause":False,"user_mail":False,"save_path":rs.DocumentPath().replace(".3dm","_gcode.txt") if rs.DocumentPath() else False,"selected_preset":False} if not userData else userData
        
        if not self.user_data["technical_name"]: self.user_data["technical_name"]=  rs.DocumentName().replace(".3dm","_gcode")
        if not self.user_data["name_url"]:self.user_data["name_url"] =  rs.DocumentName().replace(".3dm","")
        
        try:
            token = um.get_login_token()
            self.user_data["spkcam_session_token"] = token 
            self.user_data["user_mail"] = um.get_user()
           
        except:
            self.user_data["spkcam_session_token"] = False
            self.user_data["user_mail"] = False
        
        self.form = Meier_UI_Utility.UIForm("SPKCAM:.") 
        self.addControls()
        self.form.layoutControls()
        self.print_initial_state()
        
        #self.select_button(False, False)
        #self.make_code_button(False,False)

    def addControls(self):
        # The controls get added to the panel of the form
        p = self.form.panel
        p.addPictureBox("picbox1", IMAGE_FOLDER + "Logo-linarand.png" if self.user_data["user_mail"] and self.user_data["user_mail"].endswith("ingenierialinarand.com") else IMAGE_FOLDER + "Logo-spkcam.png" , False)
        p.addLabel("", " "*50, (50, 50, 50), False)
        p.addPictureBox("picbox2", IMAGE_FOLDER + "login.png", False)
        p.addButton("login_logout", "Login" if not self.user_data["spkcam_session_token"] else "Logout",100, True, self.login_button)
        p.addLabel("version",VERSION, (50, 50, 50), False)
        p.addLinkLabel("", "www.spkautomatizacion.com", "http://www.spkautomatizacion.com", True, None)
        p.addLabel("login_text", TXT["login"] if not self.user_data["user_mail"] else self.user_data["user_mail"],(100, 100, 100),True)
        #p.addLabel("", "LINARAND SPK:. Generador CodigoG 1.b 2016",(100, 100, 100), True)
        p.addPictureBox("picbox2", IMAGE_FOLDER + "curves.png", False)
        
        p.addButton("select", TXT["selobjbutton"],206, False, self.select_button)
        p.addLabel("sel_objects",TXT["selobj_res_no"],(100, 100, 100),True)

        p.addPictureBox("picbox2", IMAGE_FOLDER + "preset.png", False)

        p.addButton("sel_preset",TXT["sel_r"],206, False, self.sel_preset_button)
        p.addLabel("preset",self.user_data["selected_preset"] if self.user_data["selected_preset"] else TXT["sel_r_no"], (100, 100, 100), True)
        
        p.addPictureBox("picbox2", IMAGE_FOLDER + "new.png", False)
        p.addButton("new_settings", TXT["nr"],100, False, self.new_settings_button)
        p.addPictureBox("picbox2", IMAGE_FOLDER + "edit.png", False)
        p.addButton("edit_settings", TXT["ed"],60, False, self.edit_settings_button)
        p.addPictureBox("picbox2", IMAGE_FOLDER + "show.png", False)
        p.addButton("show_settings", TXT["mo"],60, False, self.show_settings_button)
        p.addPictureBox("picbox2", IMAGE_FOLDER + "delete.png", False)
        p.addButton("delete_settings",TXT["bo"],60, True, self.delete_settings_button)
        
        p.addLabel("", " "*60, (50, 50, 50), True)
        
        p.addPictureBox("picbox2", IMAGE_FOLDER + "radius.png", False)
        p.addLabel("",TXT["diam"], None, False)
        p.addNumericUpDown("cut_diam", 0,15000 , .1,2,self.general_settings["cut_diam"], 60, False, self.input_setting)
        p.addLabel("", "mm", None, False)
        p.addLabel("", " "*5, (50, 50, 50), False)
        p.addPictureBox("picbox2", IMAGE_FOLDER + "cluster.png", False)
        p.addCheckBox("autocluster", TXT["autocluster"], False if not self.user_data["autocluster"] else True, True, self.change_checkbox)
        

        p.addPictureBox("picbox2", IMAGE_FOLDER + "sec_plane.png", False)

        p.addLabel("", TXT["sec"], None, False)
        p.addNumericUpDown("sec_plane", 0, 600, 1, 0,self.general_settings["sec_plane"], 60, False, self.input_setting)
        p.addLabel("", "mm", None, False)
        p.addLabel("", " "*5, (50, 50, 50), False)
        
        p.addPictureBox("picbox2", IMAGE_FOLDER + "array.png", False)
        p.addCheckBox("sorting", TXT["xy"], False if not self.user_data["sorting"] else True, True, self.change_checkbox)
        p.addPictureBox("picbox2", IMAGE_FOLDER + "rapid.png", False)

        p.addLabel("", TXT["mr"], None, False)
        p.addNumericUpDown("feed_rapid", 0,15000 , 1, 0,self.general_settings["feed_rapid"], 60, False, self.input_setting)
        p.addLabel("", "mm/min", None, False)
        
        p.addLabel("", ""*1, (50, 50, 50), False)
        p.addPictureBox("picbox2", IMAGE_FOLDER + "closest.png", False)
        p.addCheckBox("sort_closest", TXT["dist"], False if not self.user_data["sort_closest"] else True, True, self.change_checkbox)

        #p.addLabel("", " "*60, (50, 50, 50), True)
        
        p.addPictureBox("picbox2", IMAGE_FOLDER + "gcode.png", False)

        p.addButton("make_code", TXT["code"],200, False, self.make_code_button)
        p.addLabel("gcode_text", "",(100, 100, 100),True)

        p.addLabel("", " "*60, (50, 50, 50), True)
        p.addPictureBox("picbox2", IMAGE_FOLDER + "cloud.png", False)
        p.addTextBox("name_url",self.user_data["name_url"], 300, False, self.add_mail)
        p.addButton("upload_code", TXT["gt"],60, True, self.go_to_button)
        p.addPictureBox("picbox2", IMAGE_FOLDER + "gcode.png", False)
        p.addTextBox("technical_name",self.user_data["technical_name"], 300, True, self.add_technical_name)
        p.addPictureBox("picbox2", IMAGE_FOLDER + "upload.png", False)
        p.addButton("upload_code", TXT["nube"],200, False, self.upload_code_button)
        p.addCheckBox("save_file", TXT["pc"], False if not self.user_data["save_file"] else True, True, self.change_checkbox)
        p.addLabel("", " "*60, (50, 50, 50), True)
        
        p.addLabel("line_1", ""*70,(100, 100, 100),True,False)
        p.addLabel("line_2", ""*70,(100, 100, 100),True,False)
        p.addLabel("line_3", ""*70,(100, 100, 100), True,False) 
        #p.addReadonlyText(name, text, width, breakFlowAfter)
        #p.addLabel("upload_text", "No hay registro de uploads.",(100, 100, 100),True)
        #p.addLabel("code_text", "No hay registro de archivos guardados.",(100, 100, 100),True)
        #p.addLabel("path", self.user_data["save_path"][-50:] if self.user_data["save_path"] else "Sin ruta de archivo.",(100, 100, 100), True)     

    
    def add_line(self,line):
        
        self.terminal_lines.append(line[-60:])
        self.form.panel.Controls.Find("line_1", True)[0].Text = self.terminal_lines[-3]
        self.form.panel.Controls.Find("line_2", True)[0].Text = self.terminal_lines[-2]
        self.form.panel.Controls.Find("line_3", True)[0].Text = self.terminal_lines[-1]
      
    
    def print_initial_state(self):
        self.add_line(TXT["init"])
        self.add_line(TXT["lfo"]) if self.user_data["user_mail"]  else self.add_line(TXT["login"])
        self.add_line(os.path.dirname(os.path.realpath(__file__)))
    
    def go_to_button(self,sender,e):
        
        if self.user_data["name_url"]:
            if spk_page in self.user_data["name_url"]:
                webbrowser.open_new(self.user_data["name_url"])
        else:
            webbrowser.open_new(spk_page+"/my-cloud")
    
    def login_button(self,sender,e):
        
        if sender.Text == "Login":
            if self.login_thread == False:
                self.login_thread = LoginThread()
                self.login_thread.start()
                thread.start_new_thread(self.wait_login_thread,(False,False,sender))
                self.form.panel.Controls.Find("login_text", True)[0].Text =TXT["abrexp"]

            else:
                if not self.login_thread.isAlive():
                    self.login_thread = LoginThread()
                    self.login_thread.start()
                    thread.start_new_thread(self.wait_login_thread,(False,False,sender))
                    self.form.panel.Controls.Find("login_text", True)[0].Text = TXT["abrexp"]
                else:
                    self.form.panel.Controls.Find("login_text", True)[0].Text = TXT["loproc"]
        else:
            thread.start_new_thread(self.wait_login_thread,(False,False,sender))
            self.form.panel.Controls.Find("login_text", True)[0].Text = TXT["looutproc"]
            
    def wait_login_thread(self,threadName,delay,sender):
        
        if sender.Text == "Login":
            while self.login_thread.isAlive():
                if self.login_thread.user_mail:
                        self.user_data["user_mail"] = self.login_thread.user_mail
                        self.user_data["spkcam_session_token"] = um.get_login_token()
                        sender.Text = "Logout"
                        self.form.panel.Controls.Find("login_text", True)[0].Text = self.user_data["user_mail"] 
            if not self.user_data["spkcam_session_token"]:
                self.form.panel.Controls.Find("login_text", True)[0].Text = TXT["tmpex"]
                  
                    
        else:
            um.logout()
            self.user_data["user_mail"] = None
            self.user_data["spkcam_session_token"] = None
            sender.Text = "Login"
            self.form.panel.Controls.Find("login_text", True)[0].Text = TXT["login"]

    def save_image(self):

        save_path = SNAPSHOT_FOLDER + "_SnapShot2.png"
        save_path_2 = SNAPSHOT_FOLDER + "_SnapShot1.png"
        persp_view = "Perspective"
        top_view = "Top"
        desire_width = 1800
        
        views = rs.ViewNames()
        
        try:
            if views:
                persp_view = views[0]
                top_view = views[1]
            width,height = rs.ViewSize(persp_view)
            scale = int(desire_width/width)
            image_size = (width*scale,height*scale)
            #rs.CurrentView(persp_view)
            rs.CreatePreviewImage(save_path, view=persp_view, size=image_size, flags=2, wireframe=False)
            #rs.Command("-_ViewCaptureToFile %s Width=%s  Height=%s  Scale=%s  DrawGrid=%s  DrawWorldAxes=%s  DrawCPlaneAxes=%s  TransparentBackground=%s _Enter" %(save_path,width,height,scale,"No","Yes","Yes","Yes"))
            width,height = rs.ViewSize(top_view)
            scale = int(desire_width/width)
            #rs.CurrentView(top_view)
            rs.CreatePreviewImage(save_path_2, view=top_view, size=image_size, flags=2, wireframe=False)
            #rs.Command("-_ViewCaptureToFile %s Width=%s  Height=%s  Scale=%s  DrawGrid=%s  DrawWorldAxes=%s  DrawCPlaneAxes=%s  TransparentBackground=%s _Enter" %(save_path_2,width,height,scale,"No","Yes","Yes","Yes"))
            return save_path,save_path_2
        except:
            return False
    
    def upload_code_button(self,sender,e):
        if self.code_thread:
            rs.MessageBox(TXT["error_wait"],0)
            return
        if not self.spkmodel_objects:
            rs.MessageBox(TXT["error_generate"],0)
            return
        if not self.user_data["name_url"]:
            rs.MessageBox(TXT["error_input"],0)
            return
        
        self.add_line(TXT["uploading"])
      
        save_file = self.user_data["save_file"]
        if save_file:
            save_path = rs.SaveFileName(TXT["save_file"],None, rs.DocumentPath() if not self.user_data["save_path"] else self.user_data["save_path"] ,"%s_gcode" % self.user_data["name_url"] if "www" not in self.user_data["name_url"] else "", ".txt")
            if not save_path:
                return
        else:
            save_path = TEMP_GCODE_FILE
            
        self.user_data["save_path"] = save_path
        
        thread.start_new_thread(self.upload_thread,(False,False,self.save_image()))
    
    def read_info_file(self,file_name):
        file_path = os.path.join("\\".join(rs.DocumentPath().split("\\")[:-1]),file_name)
        if not os.path.isfile(file_path): file_path = os.path.join("\\".join(rs.DocumentPath().split("\\")[:-1]),file_name + ".txt")
        if os.path.isfile(file_path):
            f = open(file_path)
            info_file_path = json.loads(f.read())
            f.close()
            return info_file_path
        else: return False
    
    def upload_thread(self,threadName,delay,images):
    
        #url=requests.post(base_url,data={"script_password":script_password}).text.strip()
        #print url
        
        self.write_code_button(False, False)
        gcode_file = open(self.user_data["save_path"],"rb") 
        
        if not self.user_data["user_mail"]:
            rs.MessageBox(TXT["error_login"],0)
            return
        
        data={
         "spkcam_session_token":self.user_data["spkcam_session_token"],
         "price":"0",   
            "new_gcodes_number":"1",
            "description": "SPKCAM:. Uploader",
            "labels":"spkcam_upload,temporal,upload",
            "technical_description_new_0":self.machining_settings[self.user_data["selected_preset"]]["material_info"]if self.user_data["selected_preset"] else gcode_file.read()[:50],
            "g_code_name_new_0": "%s-%s" % (self.user_data["selected_preset"],self.user_data["save_path"].split("\\")[-1]) if not self.user_data["technical_name"] else self.user_data["technical_name"],
            "new_gcode_file_0":gcode_file,
            }
        
        drive_info = self.read_info_file("spkcam_data")
        if drive_info: 
    
            data["drive_folder"]=drive_info["drive_id"]
            data["labels"] = "%s,%s" % (data["labels"],drive_info["labels"])
            data["description"] = str(drive_info["description"].decode("utf-8","replace"))
            data["technical-description"]=drive_info["technical-description"]
            
        openimages = []
       
        if spk_page in self.user_data["name_url"]:
            data["pid"] = self.user_data["name_url"].split("/")[-1]

        else: 
            data["nombre"]=self.user_data["name_url"]
            if images:
                data=zip(data.keys(),data.values())
                for image in images:
                    openimage = open(image,"rb")
                    openimages.append(openimage)
                    data.append(("files",openimage))
                    
        try:
            opener = urllib2.build_opener(MultipartPostHandler.MultipartPostHandler)
            url = opener.open(base_url, data).read()
            spk_response = opener.open(url, data).read()
            
            
            if  self.user_data["name_url"] == spk_page + spk_response:
                self.add_line("Se agrego codigo al producto" )
            else:
                self.add_line(TXT["new_product"])
                
            self.user_data["name_url"] = spk_page + spk_response
            self.form.panel.Controls.Find("name_url", True)[0].Text =  self.user_data["name_url"]
        except ZeroDivisionError:
            self.add_line(TXT["error_coneccion"])
        
        if openimages:
            for image in openimages:
                image.close()
        
        
    def change_checkbox(self,sender,e):

        self.user_data[sender.Name] = sender.Checked
    

    def write_code_button(self,sender,e):
        
        if self.spkmodel_objects:
            if self.user_data["save_path"]:
                gcode = IN_TEXT + ["(%s)"%self.user_data["selected_preset"],"(<%s>)"%self.time,"G0Z%sF%s" % (self.general_settings["sec_plane"],self.general_settings["feed_rapid"])]

                for rhinoobject in self.sorted_objects:
                    gcode += rhinoobject.gcode    
                gcode += OUT_TEXT

                time = vectors_from_gcode(gcode,preview=False,only_time=True)
                self.add_line("%s %s mins" % (TXT["time_txt"],time))
                
                f=open(self.user_data["save_path"],"w")
                f.write("\n".join(gcode))
                f.close()
            else:
                self.file_name_button(False,False)
                self.write_code_button(False, False)
            self.add_line(TXT["file_saved"])
            return True
        
        else:
            rs.MessageBox(TXT["error_generate"],0)
            return False
                   
    def index_code_button(self,sender,e):
        
        if self.spkmodel_objects:
            if self.user_data["save_path"]:
                
                f=open(self.user_data["save_path"],"r")
                previus_gcode = f.read()
                total_time =  float(previus_gcode[previus_gcode.index("<")+1:previus_gcode.index(">")]) + self.time
                
                previus_gcode = previus_gcode[:previus_gcode.index("<")] + "<%s>" %str(total_time) + previus_gcode[previus_gcode.index(">")+1:]
                
                if "(ending)" in previus_gcode:
                    previus_gcode = previus_gcode[:previus_gcode.index("(ending")]
                f.close()
                
                gcode = []

 
                for rhinoobject in self.sorted_objects:
                    gcode += rhinoobject.gcode
                gcode += OUT_TEXT
                
                f=open(self.user_data["save_path"],"w")
                f.write(previus_gcode + "(%s)\n%s\n" % (self.user_data["selected_preset"],"(None)" if not self.user_data["index_pause"] else "!") + "\n".join(gcode))
                f.close()
            else:
                self.file_name_button(False,False)
            
            
            self.form.panel.Controls.Find("gcode_text", True)[0].Text = "Tiempo actualizado: %s mins" % str(int(total_time))
            self.add_line("Archivo indexado")
        else:
            rs.MessageBox(TXT["error_generate"],0)
    
        
    def add_mail(self,sender,e):
        self.user_data[sender.Name] =  sender.Text.replace("mail:","").replace("nombre/url:","").strip()
    
    def add_technical_name(self,sender,e):
        self.user_data[sender.Name] =  sender.Text
    
    def file_name_button(self,sender,e):
        save_path = rs.SaveFileName(TXT["save_file"],None, rs.DocumentPath() if not self.user_data["save_path"] else self.user_data["save_path"] ,"%s_gcode" % rs.DocumentName().replace(".3dm",""), ".txt")
        if save_path:
            self.add_line(save_path)
        else:
            pass
    def show_settings_button(self,sender,e):
        
        if self.user_data["selected_preset"]:
            titles = [str(i) for i in self.machining_settings[self.user_data["selected_preset"]]]
            string = ""
            for title in titles:
                if title != "persistant":
                    string += title + "\n   "
                    string += "\n   ".join([str(e) + " -  " +str(i) for i, e in self.machining_settings[self.user_data["selected_preset"]][title].iteritems()])
                    string += "\n\n"
            rs.MessageBox(string,0,TXT["conf"])
            
    def delete_settings_button(self,sender,e):
        if self.user_data["selected_preset"]:
            if rs.MessageBox("Delete %s" % self.user_data["selected_preset"], 4 | 32) == 6:
                w =self.form.panel.Controls.Find("preset", True)[0]
                w.Text = "%s %s" % (self.user_data["selected_preset"],TXT["del"])
                del self.machining_settings[self.user_data["selected_preset"]] 
                self.user_data["selected_preset"] = None
          
          
    def sel_preset_button(self,sender,e):
        
        preset =  rs.ListBox(sorted(["* %s"%i if self.machining_settings[i]["persistant"] else "%s"%i for i in self.machining_settings]), message="Rutinas:", title="Cambiar rutina", default=None)
        try:
            w = self.form.panel.Controls.Find("preset", True)[0]
            if preset:
                
                self.user_data["selected_preset"] = preset.replace("*","").strip()
                w.Text = preset
            else:
                pass
        except:
            pass

    def input_setting(self,sender, e):
        
        #print sender.Name + " " + sender.Value.ToString()
        self.general_settings[sender.Name] = float(sender.Value.ToString())
        value = sender.Value.ToString()
    
    def edit_settings_button(self,sender,e,edit=False):

        while True:
            name = rs.StringBox (message=TXT["name"], default_value=self.user_data["selected_preset"], title=TXT["nueva"])
            if name == self.user_data["selected_preset"]:
                break
            else:
                if name != "" and name not in self.machining_settings:
                    break        
        if name:
            machining_settings = {name:{}}
            for compensation in [key for key in INPUT_VALUES]:
                machining_settings[name][compensation] =  {}
               
                list_settings = rs.PropertyListBox([i for i in INPUT_VALUES[compensation]],[str(self.machining_settings[self.user_data["selected_preset"]][compensation][i]) for i in VARIABLE_NAMES[compensation]],compensation, TXT["cutconf"])
                if list_settings:
                    for i in range(0,len(list_settings)):
                        
                        machining_settings[name][compensation][VARIABLE_NAMES[compensation][i]] = self.validate_data(list_settings[i], VARIABLE_NAMES[compensation][i])
                else:
                    return
            persistant = rs.MessageBox(TXT["save_pers"], 4 | 256 | 64,TXT["database"])
            
            if persistant == 6:
                machining_settings[name]["persistant"] = False
            else:
                machining_settings[name]["persistant"] = True
            
            del self.machining_settings[self.user_data["selected_preset"]] 
            self.form.panel.Controls.Find("preset", True)[0].Text = name
            
            self.machining_settings.update(machining_settings)
            self.user_data["selected_preset"] = name

    def validate_data(self,in_value,var_name):
        
        try:
            in_value = float(in_value)
        except:
            return in_value
        
        if var_name in ["feed","feed_cut","feed_plunge","entries","plunge"]:    
            if in_value < 1:
                in_value = 1.0
        if var_name in ["xy_dist"]:
            if in_value < .1 or in_value > 1:
                in_value = .5
        if var_name in ["depth"]:
            if in_value > -.01:
                in_value = in_value * -1
                
        return in_value
    
    def new_settings_button(self,sender,e,edit=False):
        
        while True:
            name = rs.StringBox (message=TXT["name"], default_value=None, title=TXT["nueva"])
            if name != "" and name not in self.machining_settings:
                break
        if name:
            machining_settings = {name:{}}
            for compensation in [key for key in INPUT_VALUES]:
                machining_settings[name][compensation] =  {}
                if self.user_data["selected_preset"]:
                    list_settings = rs.PropertyListBox([i for i in INPUT_VALUES[compensation]],[str(self.machining_settings[self.user_data["selected_preset"]][compensation][i]) for i in VARIABLE_NAMES[compensation]],compensation, "Configuracion de corte")
                else:
                    list_settings = rs.PropertyListBox([i for i in INPUT_VALUES[compensation]],[0 for i in INPUT_VALUES[compensation]],compensation, "Configuracion de corte")
                if list_settings:
                    for i in range(0,len(list_settings)):
                        machining_settings[name][compensation][VARIABLE_NAMES[compensation][i]] = self.validate_data(list_settings[i], VARIABLE_NAMES[compensation][i])
                else:
                    return
            persistant = rs.MessageBox(TXT["save_pers"], 4 | 256 | 64,TXT["database"])
            
            if persistant == 6:
                machining_settings[name]["persistant"] = False
            else:
                machining_settings[name]["persistant"] = True

            self.user_data["selected_preset"] = name
            w = self.form.panel.Controls.Find("preset", True)[0]
            w.Text = name
            self.machining_settings.update(machining_settings)
            
        
    def select_button(self,sender, e):
        
        w = self.form.panel.Controls.Find("sel_objects", True)[0]
        w.Text = TXT["selobj"]
        objects = rs.GetObjects(TXT["seldesc"],7,True,True,)
        points = []
        curves_inside = []
        curves_outside = []
        curves_open = []
        curves_pocketing = []
        curve_material = False
        validated = False
        if objects:
            for object in objects:
                if rs.IsCurve(object):
                    
                    color = rs.ObjectColor(object)
                    rgb = (rs.ColorRedValue(color),rs.ColorGreenValue(color),rs.ColorBlueValue(color))
                    if rs.IsCurveClosed(object):
                        if rgb == (0,0,255):
                            validated = True
                            curves_inside.append(object)
                        if rgb == (255,0,0):
                            validated = True
                            curves_outside.append(object)
                        if rgb == (255,0,255):
                            validated = True
                            curves_pocketing.append(object)
                        if rgb == (0,255,255):
    
                            curve_material = object
                    
                    if rgb == (0,255,0):
                        validated = True
                        curves_open.append(object)
                
                if rs.IsPoint(object):
                    validated = True
                    points.append(object)
                    
        if validated:
            self.rhino_objects = {"points":points,"curves_open":curves_open,"curves_pocketing":curves_pocketing,"curves_inside":curves_inside,"curves_outside":curves_outside,"curve_material":curve_material}
            try:
                w = self.form.panel.Controls.Find("sel_objects", True)[0]
                obj = 0
                for key in self.rhino_objects:
                    if self.rhino_objects[key]:
                        obj += len(self.rhino_objects[key])
                texts = "%s %s" % (str(obj),TXT["selobj_res"])
                w.Text = texts
            
            except:
                pass
        else:
            try:
                w = self.form.panel.Controls.Find("sel_objects", True)[0]
                w.Text = TXT["selobj_res_no"]
            
            except:
                pass
        rs.UnselectAllObjects()
    
    def clean_layers(self):
        
        try:
            rs.LayerLocked(PREVIEW_LAYER_NAME,False)
            rs.LayerLocked(LAYER_CLUSTER,False)
            rs.LayerLocked(LAYER_SORTING,False)
            rs.DeleteObjects(rs.ObjectsByLayer(PREVIEW_LAYER_NAME))
            rs.DeleteObjects(rs.ObjectsByLayer(LAYER_CLUSTER))
            rs.DeleteObjects(rs.ObjectsByLayer(LAYER_SORTING))
        except:
            preview_layer = rs.AddLayer(PREVIEW_LAYER_NAME, color=0, visible=True, locked=True, parent=None)
            rs.AddLayer(LAYER_SORTING, color=0, visible=True, locked=True, parent=preview_layer)
            rs.AddLayer(LAYER_CLUSTER, color=0, visible=True, locked=True, parent=preview_layer)
                
        rs.LayerLocked(PREVIEW_LAYER_NAME,True)
        rs.LayerLocked(LAYER_SORTING,True)
        rs.LayerLocked(LAYER_CLUSTER,True)


    def make_code_button(self,sender,e):
        self.form.panel.Controls.Find("gcode_text", True)[0].Text = TXT["gencode"]
        self.code_thread = True
        #thread.start_new_thread(self.make_code_thread,(False,False))
        #self.make_code_thread(False,False)
        self.clean_layers()
 
        if self.user_data["selected_preset"] and self.rhino_objects:
            spkmodel_objects = {}
            for colorcode, objects in self.rhino_objects.iteritems():
                if objects:
                    spkmodel_objects[colorcode] =[]
                    for rh_object in objects:
                        try:
                            rs.UnselectAllObjects()
                            if colorcode == "points":
                                curve = g_curve(rh_object,self.machining_settings[self.user_data["selected_preset"]]["barrenado"],self.general_settings,0,False)
                            if colorcode == "curves_open":
                                curve = g_curve(rh_object,self.machining_settings[self.user_data["selected_preset"]]["grabado"],self.general_settings,0,False)
                            if colorcode == "curves_pocketing":
                                curve = g_curve(rh_object,self.machining_settings[self.user_data["selected_preset"]]["desbaste"],self.general_settings,-1,True)
                                #rs.ObjectLayer(curve.cut_curve,PREVIEW_LAYER_NAME)
                            if colorcode == "curves_outside":
                                curve = g_curve(rh_object,self.machining_settings[self.user_data["selected_preset"]]["corte"],self.general_settings,1,False)
                                #rs.ObjectLayer(curve.cut_curve,PREVIEW_LAYER_NAME)
                            if colorcode == "curves_inside":
                                curve = g_curve(rh_object,self.machining_settings[self.user_data["selected_preset"]]["corte"],self.general_settings,-1,False)
                                #rs.ObjectLayer(curve.cut_curve,PREVIEW_LAYER_NAME)
                            spkmodel_objects[colorcode].append(curve)
                        except ZeroDivisionError:
                            if rs.IsObject(rh_object):
                                dot = rs.AddTextDot("Error",rs.CurveStartPoint(rh_object) if not rs.IsPoint(rh_object) else rh_object)  
                                rs.ObjectLayer(dot,PREVIEW_LAYER_NAME)
                                objects_remaining = rs.ObjectsByLayer(OFFSET_LAYER)
                                if objects_remaining:
                                    rs.DeleteObjects(objects_remaining)
            self.spkmodel_objects = spkmodel_objects
            objects_remaining = rs.ObjectsByLayer(OFFSET_LAYER)
            if objects_remaining:
                rs.DeleteObjects(objects_remaining)
            thread.start_new_thread(self.make_code_thread,(False,False))
            
        else:
            rs.MessageBox(TXT["selobj_res_no"],0)
            self.form.panel.Controls.Find("gcode_text", True)[0].Text = "Error" 
        
    def make_code_thread(self,threadName,delay):

        object_list = []
        
        for e, i in self.spkmodel_objects.iteritems():
            for rhinoobject in i:
                if not rs.IsPoint(rhinoobject.start_point):
                    rhinoobject.start_point = rs.AddPoint(rhinoobject.start_point)
                    
                object_list.append((rhinoobject,rs.PointCoordinates(rhinoobject.start_point)[0],rs.PointCoordinates(rhinoobject.start_point)[1]))

        if self.user_data["sorting"]:
            object_list = [i[0] for i in sorted(object_list, key = operator.itemgetter(2, 1))]
        else:
            object_list = [i[0] for i in object_list]
        
        if self.user_data["sort_closest"] and len(object_list) > 1:
            object_list = self.closest_points(object_list)
        #self.closest_points(object_list)    
        
        if self.user_data["autocluster"]:
            self.asign_clusters()
            cluster_list = []
            for spkmodelobject in object_list:
                if spkmodelobject.asignedcluster == -1:
                    cluster_list.append(spkmodelobject)
                if spkmodelobject.type == "curve":
                    if spkmodelobject.iscluster:
                        for cluster_object in object_list:
                            if cluster_object.asignedcluster == spkmodelobject.asignedcluster:
                                if cluster_object.type == "curve":
                                    if cluster_object.iscluster == False: 
                                        cluster_list.append(cluster_object)
                                else:
                                    cluster_list.append(cluster_object)
                        cluster_list.append(spkmodelobject)
            object_list = cluster_list
        
        time = 0       
        count = 0
        ccount = 0
        for rh_object in object_list:
            if self.code_thread:
                rh_object.process()
                if rh_object.type == "curve":
                    if rh_object.iscluster:
                        cluster_dot = rs.AddTextDot("cluster: %s"%ccount,rh_object.point)
                        rs.ObjectLayer(cluster_dot,LAYER_CLUSTER)
                        ccount +=1
                    
                rs.ObjectLayer(rh_object.preview,PREVIEW_LAYER_NAME)
                dot = rs.AddTextDot(str(count),rh_object.start_point)
                rs.DeleteObject(rh_object.start_point)
                rs.ObjectLayer(dot,LAYER_SORTING)
                rs.ObjectColor(dot,(100,100,100))
                time += rh_object.time
                count += 1
            else:
                break
        self.time = time    
        self.sorted_objects = object_list
        self.form.panel.Controls.Find("gcode_text", True)[0].Text = TXT["gencodeok"]
        self.code_thread = False  


    
    def closest_points(self,rh_objects):
        closest_list = []
        
        test_object = rh_objects[0]
        closest_list.append(test_object)
        while True:
            if len(rh_objects) == 0:
                break
            rh_objects.pop(rh_objects.index(test_object))
            if len(rh_objects) == 0:
                break
            
            closest_point_index = rs.PointArrayClosestPoint([rs.PointCoordinates(i.start_point) for i in rh_objects],test_object.point)
            closest_object = rh_objects[closest_point_index]
            closest_list.append(closest_object)
            test_object = closest_object
        #rs.DeleteObjects([point for point in point_cloud])
        return closest_list
    
    def asign_clusters(self):
        
        geometry = []
        for e,i in self.spkmodel_objects.iteritems():
            if e != "curves_outside":
                for rh_object in i:    
                    geometry.append(rh_object)
        try:
            if self.spkmodel_objects["curves_outside"]:
                count = 0
                for curve in self.spkmodel_objects["curves_outside"]:
                    for point in geometry:
                        if point.asignedcluster == -1:
                            if rs.PointInPlanarClosedCurve(point.point,curve.curve):
                                point.asignedcluster = count
                                curve.asignedcluster = count
                                curve.iscluster = True
                            else:
                                pass
                            
                    count += 1
        except:
            pass
        


    


def Main():
    
    if not LANG: return
        
    if not rs.IsLayer(OFFSET_LAYER):
        rs.AddLayer(OFFSET_LAYER)
    else:
        rs.DeleteObjects(rs.ObjectsByLayer(OFFSET_LAYER))
    if not rs.IsLayer(TRASH_LAYER):
        rs.AddLayer(TRASH_LAYER)
    else:
        rs.DeleteObjects(rs.ObjectsByLayer(TRASH_LAYER))

    original_layer = rs.CurrentLayer()
    
    machining_settings = False
    general_settings = False
    user_data = False
    

#     if rs.IsAlias(alias_name):
#         if rs.AliasMacro(alias_name) != "-_RunPythonScript (\"%s\")" % os.path.realpath(__file__):
#             if rs.MessageBox("Rhino tiene registrado esta ubicacion en el comando de %s:\n\n%s\n\nDeseas cambiarla por esta?\n\n%s\n" % (alias_name,rs.AliasMacro(alias_name),os.path.realpath(__file__)) , 4 | 32) == 6:
#                 rs.DeleteAlias(alias_name)
#                 rs.AddAlias(alias_name,"-_RunPythonScript (\"%s\")" % os.path.realpath(__file__))
#             else:
#                 pass
#     else:
#         if rs.MessageBox("Vincular el comando \"%s\" a este archivo?\n\n%s\n\nPodras ejecutar directamente el plugin escribiendo \"%s\" en la consola." %  (alias_name,os.path.realpath(__file__),alias_name) , 4 | 32) == 6:
#             rs.AddAlias(alias_name,"-_RunPythonScript (\"%s\")" % os.path.realpath(__file__))
#         else:
#             pass

    try:
        machining_settings =  eval(rs.GetDocumentData(REGISTRY_SECTION,"machining_settings"))
   
    except:
        pass
    try:
        general_settings =  eval(rs.GetDocumentData(REGISTRY_SECTION,"general_settings"))
    except:
        pass
    try:
        
        f = open(SETTINGS_FILE,"r")
        r = f.read()
        f.close()
        persistant = eval(r)        
        
        if machining_settings != False:
            machining_settings.update(persistant)
        else:
            machining_settings = persistant
    except:
        pass
    try:
        user_data =  eval(rs.GetDocumentData(REGISTRY_SECTION,"user_data"))
        if not user_data["save_path"]:
            user_data["save_path"] = rs.DocumentPath().replace(".3dm","_gcode.txt") if rs.DocumentPath() else False
    except:
        pass
    
    if user_data and user_data["selected_preset"] not in machining_settings:
        user_data["selected_preset"] = False
   
    print TXT["init"]
    
    ui = SettingsControl(general_settings,machining_settings,user_data)
    Rhino.UI.Dialogs.ShowSemiModal(ui.form)

    temporal = {}
    persistant = {}
    
    for name in ui.machining_settings:

        if ui.machining_settings[name]["persistant"]:
            temporal[name] = ui.machining_settings[name]
        else:
            persistant[name] = ui.machining_settings[name]
    
    f = open(SETTINGS_FILE,"w")
    f.write(str(persistant))
    f.close()
    
    rs.SetDocumentData(REGISTRY_SECTION,"machining_settings",str(temporal))
    rs.SetDocumentData(REGISTRY_SECTION,"general_settings",str(ui.general_settings))
    rs.SetDocumentData(REGISTRY_SECTION,"user_data",str(ui.user_data))

#     print "to registry...."
#     print "machining_settings",str(ui.machining_settings)
#     print "general_settings",str(ui.general_settings)
#     print "user_data",str(ui.user_data)
#     print "temp",str([i for i in temporal])
#     print "persistant",str([i for i in persistant])
    
    ui.code_thread = False
    rs.CurrentLayer(original_layer)
    rs.DeleteObjects(rs.ObjectsByLayer(OFFSET_LAYER))
    rs.DeleteObjects(rs.ObjectsByLayer(TRASH_LAYER))
    rs.DeleteLayer(OFFSET_LAYER)
    rs.DeleteLayer(TRASH_LAYER)
    
    print TXT["bye"]
    
    
Main()

