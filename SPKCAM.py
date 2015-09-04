import rhinoscriptsyntax as rs
import operator
import Rhino
import os
import urllib2
import subprocess
import sys
import json

POINT_INPUT_VALUES = ["Diametro cortador o broca:",
            "Feed mm/min:",
            "Profundidad barreno (Negativo):"]
            
CURVE_INPUT_VALUES = ["Diametro Cortador:",
            "Profundidad corte (Negativo):",
            "Numero de pasadas:",
            "Pasada en nivel 0?:",
            "Distancia aproximacion:",
            "Plunge mm lineales:",
            "Feed mm/min:",
            "Plunge mm/min:"]

CURVE_POCKETING_VALUES = ["Diametro Cortador:",
            "Profundidad corte (Negativo):",
            "Numero de pasadas en Z:",
            "Distancia entre pasadas XY(mm):",
            "Pasada en nivel 0?:",
            "Distancia aproximacion:",
            "Plunge mm lineales:",
            "Feed mm/min:",
            "Plunge mm/min:"]
    
ENGRAVING_INPUT_VALUES= ["Profundidad corte (Negativo):",
            "Numero de pasadas:",
            "Pasada en nivel 0?:",
            "Feed mm/min:",
            "Plunge mm/min:"]


IN_TEXT = ["(LINARAND SPK:. Generador CodigoG 1.b 2015)","G21","G90","G54","M3"]
OUT_TEXT = ["M5","G0X0Y0","M30"]

POINT_COLOR = (255,255,255)
PLUNGE_COLOR = (200,200,200)
CUT_COLOR = (100,100,100)
ENGRAVING_COLOR = (120,120,120)

PLUNGE_PRECISION = 0.1
CLUSTER_TOLERANCE = 1

REGISTRY_SECTION = "SPKCAM"
REGISTRY_ENTRY = "_UltimoUsado"
PATH_RUTINAS = "%s\\RutinasCorte.txt" % os.path.realpath(__file__).replace("SPKCAM.py","")
PATH_WALLPAPER = "%s\\SPK_Wallpaper.jpg" % os.path.realpath(__file__).replace("SPKCAM.py","")
PATH_HELP = "%s\\HelpTemplate.3dm" % os.path.realpath(__file__).replace("SPKCAM.py","")
PREVIEW_LAYER_NAME = "GCode_Preview_SPK:."
PROTECTED_SETTING = "GENERICO"

def get_sec_plane(objects):
    
    print objects
    z_points = []
    for group in objects:
        if group > 1:
            for object in group:
                if rs.IsCurve(object):
                    z_points.append(rs.CurveStartPoint(object)[2])
                if rs.IsPoint(object):
                    z_points.append(rs.PointCoordinates(object)[2])
        else:
            if rs.IsCurve(group):
                z_points.append(rs.CurveStartPoint(group)[2])
            if rs.IsPoint(group):
                z_points.append(rs.PointCoordinates(group)[2])
            
        
    print z_points
    try:
        return z_points.sort()[0]+6
    except:
        return z_points[0]+6
    
        
def colect_objects():
    
    print "Linarand SPK:. Gcode Generator 1.b 2015"
    objects = rs.GetObjects("Selecciona objectos (curvas/puntos):",7,True,True,)
 
    points = []
    curves_inside = []
    curves_outside = []
    curves_open = []
    curves_pocketing = []
    curve_material = False
    if objects:
        for object in objects:
            if rs.IsCurve(object):
                
                color = rs.ObjectColor(object)
                rgb = (rs.ColorRedValue(color),rs.ColorGreenValue(color),rs.ColorBlueValue(color))
                if rs.IsCurveClosed(object):
                    if rgb == (0,0,255):
                        curves_inside.append(object)
                    if rgb == (255,0,0):
                        curves_outside.append(object)
                    if rgb == (255,0,255):
                        curves_pocketing.append(object)
                    if rgb == (0,255,255):
                        curve_material = object
                
                if rgb == (0,255,0):
                    curves_open.append(object)
            
            if rs.IsPoint(object):
                points.append(object)
                
        return points,curves_open,curves_pocketing,curves_inside,curves_outside,curve_material
        
    else:
      return False
      
##Se usa para convertir los strings de settings a numeros enteros
def input_to_number(input_data):
    input = []
    for i in input_data:
        try:
            input.append(float(i))
        except ValueError:
            input.append(i)
    return input #

def upload_to_server(save_path,settings_path,image_1,image_2,user,price):
    
    #print "python " + "\"" + sys.path[0] + "\\Upload.py " + "\"" + save_path + "\"  \"" +  settings_path +"\" " +image_1 + " " + image_2 + " " + user
    subprocess.call("python " +  "\"" + sys.path[0] + "\\Upload.py\" " + "\"" + save_path + "\"  \"" +  settings_path +"\" " +image_1 + " " + image_2 + " " + user + " " + str(price))
    print "Archivo guardado en el servidor"
    
def save_file(g_code,autoname):

    if autoname.lower().strip() == "no":
        save_path = rs.SaveFileName("Selecciona donde guardar el codigo",".txt|Filter1|.nc|Filter2||", rs.DocumentPath(),"%s-SPKCAM_CodigoG.txt" % (rs.DocumentName().replace(".3dm","")), ".txt")
    else:
        if rs.DocumentPath():
            save_path = rs.DocumentPath().replace(rs.DocumentName(),"%s-SPKCAM_CodigoG.txt" % (rs.DocumentName().replace(".3dm","")))
        else:
            rs.MessageBox("No se ha podido autonombrar el archivo. \n\nEs un buen habito guardar su archivo de Rhino antes de generar el codigo.\n(OJO: Basiiii!!!!!!)")
            save_path = rs.SaveFileName("Selecciona donde guardar el codigo",".txt|Filter1|.nc|Filter2||", rs.DocumentPath(),"%s-SPKCAM_CodigoG.txt" % (rs.DocumentName().replace(".3dm","")), ".txt")
            
    target = open(save_path, 'w')
    for line in g_code:
        target.write(line+ "\n")
        
    target.close()
    return save_path

def save_settings_file(save_path,settings,name):
    target_path = save_path.replace("CodigoG",name)
    target = open(target_path, 'w')
    target.write(settings)
    target.close()
    return target_path
    
def save_image(file_path,objectsToCapture):
    
    width = 1366
    heigth = 768
    
    save_path = "\"" + file_path.replace("_CodigoG.txt","_SnapShot1.png\"")
    save_path_2 = "\"" + file_path.replace("_CodigoG.txt","_SnapShot2.png\"")

    
    print save_path
    print save_path_2
    rs.Wallpaper("Top", PATH_WALLPAPER)
    rs.Wallpaper("Perspective", PATH_WALLPAPER)
    rs.WallpaperHidden ("Top", False)
    rs.WallpaperHidden ("Perspective", False)
    rs.Command("_SetActiveViewport Top _Enter")

    #rs.Command("-_SetDisplayMode _Viewport=Top _Mode=Rendered _Enter")
    rs.Command("-_ViewCaptureToFile " + save_path + " _Width=" + str(width) + " _Height=" + str(heigth) + " _Enter")
    #rs.Command("-_SetDisplayMode _Viewport=Top _Mode=Wireframe _Enter")
    
    rs.Command("_SetActiveViewport Perspective _Enter")
    
    #rs.Command("-_SetDisplayMode _Viewport=Perspective _Mode=Rendered _Enter")
    rs.Command("-_ViewCaptureToFile " + save_path_2 + " _Width=" + str(width) + " _Height=" + str(heigth) + " _Enter")
    #rs.Command("-_SetDisplayMode _Viewport=Perspective _Mode=Shaded _Enter")
    
    rs.WallpaperHidden ("Top", True)
    rs.WallpaperHidden ("Perspective", True)
    return save_path,save_path_2
    
class SettingsControl():
    
    def __init__(self,sec_plane):
        # Make a new form (dialog)
        self.form = Meier_UI_Utility.UIForm("SPKCAM:.") 
        self.settings = []
        self.savenew = False
        self.general_input = [sec_plane,3000,"si"]
        self.activecycle = PROTECTED_SETTING
        self.editcycle = False
        self.upload = False
        self.read_cycle_settings()
        self.cycles = self.make_cycle_list()
        self.autonameStart = self.autoname_check()
        self.addControls()
        self.textsettings = self.text_settings(self.activecycle,False)
        # Layout the controls on the formt
        self.form.layoutControls()
    # Add each control to an accumulated list of controls
    
    def autoname_check(self):
        if self.general_input[2] == "si":
            return True
        else:
            return False
    
    def make_cycle_list(self):
        
        cycles_names = []
        for key in self.settings:
            cycles_names.append(key)
        return cycles_names
                    
    def read_cycle_settings(self):
        
        rutinas_corte = {}
        with open(PATH_RUTINAS) as fp:
            for line in fp:
                line = line.replace("\n","")
                rutinas_corte.update(eval(line))
        fp.close()
        reg = rs.GetDocumentData(REGISTRY_SECTION)
        if reg:
            for entry in reg:
                if entry == "GI":
                    self.general_input = input_to_number(eval(rs.GetDocumentData(REGISTRY_SECTION,entry)))
                else:
                    if entry in rutinas_corte:
                        self.activecycle = entry
                    else:
                        if entry != "spkuser": 
                            rutinas_corte.update(eval(rs.GetDocumentData(REGISTRY_SECTION,entry)))
                            self.activecycle = entry
        
        self.settings = rutinas_corte
        
    def delete_cycle_settings(self,item_to_delete):
        
        rutinas_corte = {}
        with open(PATH_RUTINAS) as fp:
            for line in fp:
                line = line.replace("\n","")
                rutinas_corte.update(eval(line))
        fp.close()
            
        filep = open(PATH_RUTINAS,"w")

        for key in rutinas_corte.keys():
            
            if key != item_to_delete:
                line = {}
                line[key] = rutinas_corte[key]
                filep.write(str(line)+"\n")
                
        filep.close()
                
    def text_settings(self,item,simple):
        
        itemdata = self.settings[item]
        if isinstance(itemdata, dict) != True:
            itemdata = eval(itemdata)
        textitem = str(item) + ":\n"
        simpletext = textitem
        spoint = itemdata["point"]
        scurve = itemdata["curve"]
        sengraving = itemdata["engraving"]
        spocketing = itemdata["pocketing"]
        
        
        textitem += "Barrenado:\n"
        simpletext += "Barrenado:\n"
        for i in range(0,len(spoint)):
            name = POINT_INPUT_VALUES[i]
            value = spoint[i]
            textkey = "      " + name +"  "+ value + "\n"
            if i in [0,2]:
                simpletext += textkey
            textitem += textkey
        textitem += "\n"

        textitem += "Grabado:\n"
        simpletext += "Grabado:\n"
        for i in range(0,len(sengraving)):
            name = ENGRAVING_INPUT_VALUES[i]
            value = sengraving[i]
            textkey = "      " +name +"  "+ value + "\n"
            if i in [0]:
                simpletext += textkey
            textitem += textkey
        textitem += "\n"

        textitem += "Cajas:\n"
        simpletext += "Cajas:\n"
        for i in range(0,len(spocketing)):
            name = CURVE_POCKETING_VALUES[i]
            value = spocketing[i]
            textkey = "      " +name +"  "+ value + "\n"
            if i in [0,1]:
                simpletext += textkey
            textitem += textkey
        textitem += "\n"

        textitem += "Corte (interno/externo):\n"
        simpletext += "Corte (interno/externo):\n"
        for i in range(0,len(scurve)):
            name = CURVE_INPUT_VALUES[i]
            value = scurve[i]
            textkey = "      " +name + "  "+  value + "\n"
            if i in [0,1]:
                simpletext += textkey
            textitem += textkey
        textitem += "\n"

        if simple:
            return simpletext
        else:
            return textitem
    
    def addControls(self):
        # The controls get added to the panel of the form
        p = self.form.panel
        p.addPictureBox("picbox1", "./Logo-SPK-Small.png", True)
        p.addLabel("", "LINARAND SPK:. Generador CodigoG 1.b 2015",(100, 100, 100), True)
        p.addLinkLabel("", "www.spkautomatizacion.com", "http://www.spkautomatizacion.com", True, None)
        p.addButton("Ayuda", "Ayuda",50, False, self.buttonAyuda_OnButtonPress)
        p.addLabel("", "//Cargara un layer de Ayuda en Rhino", (50, 50, 50), True)
        p.addSeparator("sep1", 130, False)
        p.addLabel("", "Configuracion General", (50, 50, 50), False)
        p.addSeparator("sep2", 126, True)
        p.addLabel("", "Plano de seguridad: ", None, False)
        p.addNumericUpDown("num1", 0, 100, 1, 0, self.general_input[0], 60, False, self.num1_OnValueChange)
        p.addLabel("", "mm", None, True)
        p.addLabel("", "Movimiento rapido:   ", None, False)
        p.addNumericUpDown("num1", 0, 3000, 1, 0,self.general_input[1], 60, False, self.num2_OnValueChange)
        p.addLabel("", "mm/min", None, True)
        p.addSeparator("sep1", 130, False)
        p.addLabel("", "Rutina de maquinado", (50, 50, 50), False)
        p.addSeparator("sep1", 130, True)
        p.addComboBox("combo1",self.cycles, self.cycles.index(self.activecycle), False, self.combo1_SelectedIndexChanged)
        p.addLabel("", " "*50, (50, 50, 50), False)
        p.addButton("button1", "Borrar",50, True, self.button1_OnButtonPress)
        p.addLabel("cycleInfo",self.text_settings(self.activecycle,True), (0, 0, 0), True)
        p.addLabel("", "", (50, 50, 50), True)
        p.addButton("showbutton", "Mostrar todos",150, True, self.showbutton_OnButtonPress)
        p.addSeparator("sep1", 130, False)
        p.addLabel("", "Configuracion Archivo", (50, 50, 50), False)
        p.addSeparator("sep2", 126, True)
        p.addCheckBox("check1", "Personalizar rutina", False, False, self.check1_CheckStateChanged)
        p.addLabel("", "//Modifica y guarda la rutina en este archivo", (50, 50, 50), True)
        p.addCheckBox("check0", "Guardar rutina", False, False, self.check0_CheckStateChanged)
        p.addLabel("", "//Guarda la rutina en la base de datos de SPK:.", (50, 50, 50), True)
        p.addCheckBox("check2", "Autonombrar archivo", self.autonameStart, False, self.check2_CheckStateChanged)
        p.addLabel("", "//Guarda en tu carpeta actual", (50, 50, 50), True)
        p.addCheckBox("check3", "Subir a la nube", self.upload, False, self.check3_CheckStateChanged)
        p.addLabel("", "//Archivos temporales en ", (50, 50, 50), False)
        p.addLinkLabel("", "SPKCLoud", "http://www.spkautomatizacion.com",True, None)
        p.addSeparator("sep2", 126, True)
        p.addLabel("", " "*82, (50, 50, 50), False)
        p.addButton("OK","OK",110, False,None)
        
        #p.addCheckBox("check3", "Autonombrar", True, True, self.check1_CheckStateChanged)
    # ====================== Delegates =====================
    # Called when the box is checked or unchecked
                
    def check0_CheckStateChanged(self, sender, e):
        if self.savenew == True:
            self.savenew = False
        else:
            self.savenew = True
    def check1_CheckStateChanged(self, sender, e):
        if self.editcycle == True:
            self.editcycle = False
        else:
            self.editcycle = True
        
    def check2_CheckStateChanged(self, sender, e):
        if self.general_input[2] == "no":
            self.general_input[2] = "si"
        else:
            self.general_input[2] = "no"
      
    # Called when a selection is made from the combobox

    def check3_CheckStateChanged(self, sender, e):
        if self.upload == True:
            self.upload = False
        else:
            self.upload = True
            
    def combo1_SelectedIndexChanged(self, sender, e):
        
        index = sender.SelectedIndex # 0 based index of choice
        item = sender.SelectedItem # Text of choicetive
        self.activecycle = item
        try:
            w = self.form.panel.Controls.Find("cycleInfo", True)[0]
            texts = self.text_settings(item,True)
            w.Text = texts
            
        except:
            pass

    def showbutton_OnButtonPress(self, sender, e):
        
        rs.MessageBox(self.text_settings(self.activecycle,False),0,"Parametros de corte")

    def button1_OnButtonPress(self, sender, e):
        try:
            c = self.form.panel.Controls.Find("combo1", True)[0]
            item = c.SelectedItem
            self.form.ResumeLayout(False)
            print item + " se ha elimiado."
            self.delete_cycle_settings(item)
        except:
            pass
    # Called when the button is pressed
    
    def buttonAyuda_OnButtonPress(self, sender, e):
        
        rs.AddLayer("SPKCAM Ayuda",None)  
        rs.Command("-Import \"" + PATH_HELP + "\" _Enter")
        help_objects = rs.SelectedObjects()
        rs.ObjectLayer(help_objects,"SPKCAM Ayuda")
        rs.LayerLocked("SPKCAM Ayuda",True)
        
    def button2_OnButtonPress(self, sender, e):
        
        self.write_cycle_settings()

    # Called when the value is changed
    def num1_OnValueChange(self, sender, e):
        value = sender.Value.ToString()
        self.general_input[0] = value
            
        # Called when the value is changed
    def num2_OnValueChange(self, sender, e):
        value = sender.Value.ToString()
        self.general_input[1] = value
    # Called when the value changes
    def trackBar1_OnValueChange(self, sender, e):
        try:
            c = self.form.panel.Controls.Find("readonlyTextbox", True)[0]
            c.Text = str(sender.Value)
        except:
            pass
        
class g_point():
    
    def __init__(self,point,input_data,general_input):
        
        self.point = point
        self.asignedcluster = -1
        self.sec_plane,self.rapid,self.autoname = general_input
        self.cut_diam, self.feed, self.profundidad  = input_data
        self.gcode, self.preview = self.process_point()
        self.time = self.get_time()
    
    def get_time(self):
        
        total_length = 0
        for curve in self.preview:
            total_length += rs.CurveLength(curve)
        time = (total_length / int(self.feed))
        return time
        
    def process_point(self):
        
        strings = []
        point_preview = []
        point = rs.PointCoordinates(self.point)
        
        r_point = (round(point[0],3),round(point[1],3),round(point[2],3))
        strings.append("G0X%sY%sZ%sF%s" % (r_point[0],r_point[1],self.sec_plane,self.rapid))
        strings.append("G1X%sY%sZ%sF%s" % (r_point[0],r_point[1],r_point[2]+float(self.profundidad),self.feed))
        strings.append("G0X%sY%sZ%sF%s" % (r_point[0],r_point[1],self.sec_plane,self.rapid))
        
        start_pt = (r_point[0],r_point[1],self.sec_plane)
        end_pt = (r_point[0],r_point[1],r_point[2]+float(self.profundidad))
        pt_preview = rs.AddLine(start_pt,end_pt)
        rs.ObjectColor(pt_preview,POINT_COLOR)
        point_preview.append(pt_preview)
        
        return strings, point_preview

class g_open_curve():
    
    def __init__(self,curve,input_data,general_input):
        
        self.curve = curve
        self.asignedcluster = -1
        self.point = rs.CurveStartPoint(self.curve)
        self.depth,self.levels,self.cero_pass,self.feed,self.plunge = input_data
        self.sec_plane,self.rapid,self.autoname = general_input
        self.depth_pass = abs(float(self.depth)/int(self.levels)) 
        self.gcode, self.preview = self.process_curve()
        self.time = self.get_time()
    
    def get_time(self):
              
        total_lenght = rs.CurveLength(self.preview)
        time = (total_lenght / int(self.feed))
        return time
        
    def round_point(self,point):
        return (round(point[0],3),round(point[1],3),round(point[2],3))  
        
    def process_curve(self):
        
        curve_gcode = []
        curve_preview =[]
        
        polycurve = rs.ConvertCurveToPolyline(self.curve,0.5,0.01,False)
        point_curve = rs.CurvePoints(polycurve)

        if self.cero_pass == "si":
            start_level = 0
        else:
            start_level = 1
        
        for level in range(start_level,int(self.levels)+1):
            level_curve_gcode = []
            if level != 0:
                point_curve.reverse()
                
            if level == 0:
                point_curve[0] = self.round_point(point_curve[0])
                level_curve_gcode.append("G0X%sY%sZ%sF%s" % (point_curve[0][0],point_curve[0][1],self.sec_plane,self.rapid))
                level_curve_gcode.append("G1F%s" % self.feed)
                point_curve[0] = self.round_point(point_curve[0])
                curve_preview.append((point_curve[0][0],point_curve[0][1],self.sec_plane))
            elif level == 1 and self.cero_pass == "no":
                point_curve[0] = self.round_point(point_curve[0])
                level_curve_gcode.append("G0X%sY%sZ%sF%s" % (point_curve[0][0],point_curve[0][1],self.sec_plane,self.rapid))
                level_curve_gcode.append("G1F%s" % self.feed)
                point_curve[0] = self.round_point(point_curve[0])
                curve_preview.append((point_curve[0][0],point_curve[0][1],self.sec_plane))
            else:
                level_curve_gcode = []
 
            for point in point_curve:
                point = self.round_point(point)
                level_curve_gcode.append("X%sY%sZ%s" % (point[0],point[1],point[2]-self.depth_pass*level))
                curve_preview.append((point[0],point[1],point[2]-self.depth_pass*level))
                
            curve_gcode += level_curve_gcode
        curve_gcode.append("G1Z%s" % self.sec_plane)
        preview_line = rs.AddPolyline(curve_preview)
        rs.ObjectColor(preview_line,ENGRAVING_COLOR)
        rs.DeleteObject(polycurve)
        
        return curve_gcode,preview_line

class g_curve():
    
    def __init__(self,curve,input_data,general_input,compensation):
        inputData = input_to_number(input_data)
        try:
            int(inputData[3])
            self.cut_diam,self.depth,self.levels,self.offset,self.cero_pass,self.aproach,self.plunge_mm,self.feed,self.plunge = inputData
            self.pocketing = True
            
        except:
            self.cut_diam,self.depth,self.levels,self.cero_pass,self.aproach,self.plunge_mm,self.feed,self.plunge = inputData
            self.pocketing = False
            
        self.sec_plane,self.rapid,self.autoname = input_to_number(general_input)
        self.depth_pass = abs(float(self.depth)/int(self.levels))
        self.compensation = compensation
        self.curve = curve
        self.asignedcluster = -1
        self.iscluster = False
        self.point = rs.CurveAreaCentroid(self.curve)[0]
        self.cut_curve = self.get_cut_curve()
        self.gcode,self.preview = self.process_curve()
        self.time = self.get_time()
        
    def get_cut_curve(self):
        
        centroid = rs.CurveAreaCentroid(self.curve)[0]
         
        inside_offset = rs.OffsetCurve(self.curve,centroid,self.cut_diam/2,None)
        outside_offset = rs.OffsetCurve(self.curve,centroid,self.cut_diam/-2,None)
        
        if self.isSmall(inside_offset, outside_offset):
            
            if self.compensation == 0:
                cut_curve = self.curve
            elif self.compensation == -1:
                cut_curve = inside_offset
            elif self.compensation == 1:
                cut_curve = outside_offset
        else:
            if self.compensation == 0:
                cut_curve = self.curve
            elif self.compensation == 1:
                cut_curve = inside_offset
            elif self.compensation == -1:
                cut_curve = outside_offset
        
        try:
            cut_curve = rs.ConvertCurveToPolyline(cut_curve,0.5,0.01,False,.1)
        except:
            try:
                cut_curve = rs.ConvertCurveToPolyline(cut_curve,0.5,0.01,False)
            except:
                rs.AddTextDot("Error",rs.CurveStartPoint(self.curve))
                sys.exit()
        
        try:      
            rs.DeleteObject(outside_offset)
            rs.DeleteObject(inside_offset)
        except:
            pass
        return cut_curve

        
    def get_time(self):
        
        total_lenght = 0
        for curve in self.preview:
            total_lenght += rs.CurveLength(curve)
        time = (total_lenght / int(self.feed))
        return time
        
    def isSmall(self,curve_1,curve_2):
        if rs.CurveLength(curve_1) < rs.CurveLength(curve_2):
            return  True
        else:
            return False
            
    def round_point(self,point):
        return (round(point[0],3),round(point[1],3),round(point[2],3))
    
    def get_gcode(self,curve):
        gcode = []
        for point in rs.CurvePoints(curve):
            gcode.append("X%sY%sZ%s" % self.round_point(point))
        return gcode
        
    def get_sorted_by_size(self,curve_1, curve_2):
    
        if rs.CurveLength(curve_1) < rs.CurveLength(curve_2):
            curves = (curve_1,curve_2)
        else:
            curves = (curve_2,curve_1)
        return curves
    
    def make_pocket_curves(self,level_cut):
        
        offset_number = 10
        offset_curves = []
        last_curve = level_cut
        last_area = None
       
        while True:
            centroid = rs.CurveAreaCentroid(last_curve)[0]
            #offset_curve = rs.ScaleObject(last_curve,centroid,(scale,scale,1),True)
            offset_curve = rs.OffsetCurve(last_curve,centroid,int(self.offset),None,2)
            rs.ObjectColor(offset_curve, CUT_COLOR)
            if rs.IsCurveClosed(offset_curve[0]) != True:
                rs.DeleteObjects(offset_curve)
                break
            else:
                area = rs.CurveArea(offset_curve)
                if last_area != None and area > last_area:
                    rs.DeleteObject(offset_curve)
                    break
                offset_curves.append(offset_curve)
                last_curve = offset_curve
                last_area = area
            
        end_point = self.round_point(rs.CurveEndPoint(last_curve))
        return offset_curves,end_point
        
    def process_curve(self):
        
        curves_gcode = []
        level_preview = []
        
        cut_curve_points = rs.CurvePoints(self.cut_curve)
        
        if self.pocketing:
            offset_curves,end_point = self.make_pocket_curves(self.cut_curve)
            
        for level in range(0,int(self.levels)+1):
            new_pt = []
            for point in cut_curve_points:
                new_pt.append((point[0],point[1],point[2]-(self.depth_pass*level)))
            level_cut = rs.AddCurve(new_pt,1)
            rs.ObjectColor(level_cut,CUT_COLOR)
            domain = rs.CurveDomain(level_cut)
            length = rs.CurveLength(level_cut)
            param = ((self.plunge_mm*(level+1))*(domain[1]-domain[0]))/length
            param_2 = ((self.plunge_mm*(level+2))*(domain[1]-domain[0]))/length
            original_level_cut = rs.CopyObject(level_cut)
            rs.CurveSeam(level_cut,param)
            plunge_curve = rs.SplitCurve(level_cut,[param,param_2],False)
            plunge_points = rs.DivideCurveLength(plunge_curve[0],PLUNGE_PRECISION)
            depth_pass_plunge = (self.depth_pass)/len(plunge_points)
            
            if level == 0 and self.cero_pass =="si":
                
                mini_param = domain[0]
                mini_param_2 = ((self.plunge_mm*(level+1))*domain[1])/length
                mini_plunge_curve = rs.SplitCurve(original_level_cut,[mini_param,mini_param_2],False)
                mini_plunge_points = rs.DivideCurveLength(mini_plunge_curve[0],PLUNGE_PRECISION)
                mini_depth_pass_plunge = (mini_plunge_points[0][2]+self.aproach)/len(mini_plunge_points)

                aproach_points = []
                for point in mini_plunge_points:
                    aproach_points.append((point[0],point[1],point[2]+self.aproach))
                    
                mini_new_plunge_points = []
                z_value = 0
                for point in aproach_points:
                    mini_new_plunge_points.append((point[0],point[1],point[2]-z_value))
                    z_value += mini_depth_pass_plunge
            
                
                new_plunge_points = []
                z_value = 0
                
                for point in plunge_points:
                    new_plunge_points.append((point[0],point[1],point[2]-z_value))
                    z_value += depth_pass_plunge
                    
                plunge_curve_z = rs.AddCurve(new_plunge_points)
                mini_plunge_curve_z = rs.AddCurve(mini_new_plunge_points)
                rs.ObjectColor(plunge_curve_z,PLUNGE_COLOR)
                rs.ObjectColor(mini_plunge_curve_z,PLUNGE_COLOR)
                r_pt = self.round_point(mini_plunge_points[0])
                curves_gcode.append("G0X%sY%sZ%sF%s" % (r_pt[0],r_pt[1],self.sec_plane,self.rapid))
                curves_gcode.append("G1F%s" % (self.plunge))
                curves_gcode+=self.get_gcode(mini_plunge_curve_z)
                level_preview.append(mini_plunge_curve_z)
                curves_gcode.append("F%s" % (self.feed))
                curves_gcode+=self.get_gcode(level_cut)
                level_preview.append(level_cut)
                
                #### Anadir if de pocketing con curvas de offset aqui!!!!
                
                if self.pocketing:
                    for curve in offset_curves:
                        curves_gcode+=(self.get_gcode(curve))
                    curves_gcode.append("G0X%sY%sZ%sF%s" % (end_point[0],end_point[1],self.sec_plane,self.rapid))
                    start_next_line = rs.CurveEndPoint(level_cut)
                    curves_gcode.append("G0X%sY%sZ%sF%s" % (start_next_line[0],start_next_line[1],self.sec_plane,self.rapid))
                    level_preview += offset_curves
                    
                    
                curves_gcode.append("G1F%s" % (self.plunge))
                curves_gcode+=self.get_gcode(plunge_curve_z)
                level_preview.append(plunge_curve_z)
                rs.DeleteObjects(mini_plunge_curve)
                
                
            else:
                
                depth_pass_plunge = ((self.depth_pass))/len(plunge_points)
                aproach_points = []
                new_plunge_points = []
                z_value = 0
                
                if self.cero_pass == "no" and level == 0:
                    depth_pass_plunge = ((self.depth_pass+self.aproach))/len(plunge_points)
                    for point in plunge_points:
                        aproach_points.append((point[0],point[1],point[2]+self.aproach))
                        plunge_points = aproach_points
                        plunge_points[0] = self.round_point(plunge_points[0])
                        rs.DeleteObject(level_cut)
                    curves_gcode.append("G0X%sY%sZ%sF%s" % (plunge_points[0][0],plunge_points[0][1],self.sec_plane,self.rapid))
                
                else:

                    level_preview.append(level_cut)
                    curves_gcode.append("G1F%s" % self.feed)
                    curves_gcode+=self.get_gcode(level_cut)
                    
                    if self.pocketing:                       
                        move_vector = rs.VectorCreate((0,0,rs.CurveAreaCentroid(level_cut)[0][2]),(0,0,self.point[2]))
                        for curve in offset_curves:
                            new_curve = rs.CopyObject(curve,move_vector)
                            curves_gcode+=(self.get_gcode(new_curve))
                            level_preview.append(new_curve)
                        curves_gcode.append("G0X%sY%sZ%sF%s" % (end_point[0],end_point[1],self.sec_plane,self.rapid))
                        if level != int(self.levels):
                            start_next_line = rs.CurveEndPoint(level_cut)
                            curves_gcode.append("G0X%sY%sZ%sF%s" % (start_next_line[0],start_next_line[1],self.sec_plane,self.rapid))
                        
                
                if level == int(self.levels) and self.pocketing == False:
                    st_pt = self.round_point(rs.CurveEndPoint(level_cut))
                    curves_gcode.append("G1X%sY%sZ%sF%s" % (st_pt[0],st_pt[1],self.sec_plane,self.feed)) 
                
                if level != int(self.levels):
                    for point in plunge_points:
                        new_plunge_points.append((point[0],point[1],point[2]-z_value))
                        z_value += depth_pass_plunge
                        
                    plunge_curve_z = rs.AddCurve(new_plunge_points)
                    rs.ObjectColor(plunge_curve_z,PLUNGE_COLOR)
                    
                    level_preview.append(plunge_curve_z)
                    curves_gcode.append("G1F%s" % self.plunge)
                    curves_gcode+=self.get_gcode(plunge_curve_z)
            
            rs.DeleteObjects(plunge_curve)
            rs.DeleteObject(original_level_cut)
            rs.DeleteObject(self.cut_curve)
        if self.pocketing and self.cero_pass == "no":
                rs.DeleteObjects(offset_curves)
        return curves_gcode,level_preview

class batch():
    
    def __init__(self,objects,sec_plane):
        
        
        self.ui = SettingsControl(35)
        Rhino.UI.Dialogs.ShowSemiModal(self.ui.form)
        self.preset = self.ui.settings[str(self.ui.activecycle)]
        self.activecycle = self.ui.activecycle
        self.name = self.ui.activecycle
        if isinstance(self.preset, dict) != True:
            self.preset = eval(self.preset)
        self.general_input_data = self.ui.general_input
        self.editcycle = self.ui.editcycle
        self.savenew = self.ui.savenew
        self.upload = self.ui.upload
        self.previewobjects = []
        self.textsettings = self.ui.textsettings
        self.textinfo = self.ui.text_settings(self.ui.activecycle,True)
        #self.autocluster = self.ui.autocluster
        self.points,self.curves_open,self.curves_pocketing,self.curves_inside,self.curves_outside,self.curve_material = objects
        self.price = 0
        self.time = 0
    
    def make_log(self):
        
        settings = self.textsettings
        info = self.textinfo
        ##Saca el precio y el tiempo
        geometry = self.points + self.curves_open + self.curves_inside + self.curves_outside + self.curves_pocketing
        total_time = 0
        for object in geometry:
            total_time += object.time
        price = (total_time*(400./60.)*1.3)+100.
        self.price = int(price)
        
        textinfo = "RESUMEN:\nTiempo: " + str(round(total_time,2)) + "mins" + "\n"
        textinfo += "Material: %s \n" % self.name
        ##Saca dimensiones del material 
        if self.curve_material:

            textinfo += "Area: %sm2 \n" % (round(rs.CurveArea(self.curve_material)[0]/1000000,2))
            vertices = rs.CurvePoints(self.curve_material)
            points_x = []
            points_y = []
            for vertice in vertices:
                points_x.append(vertice[0])
                points_y.append(vertice[1])
            x_distance = sorted(points_x)[0]
            y_distance = sorted(points_y)[0]
            x = sorted(points_x)[-1] - x_distance
            y = sorted(points_y)[-1] - y_distance
            print x_distance, y_distance
            textinfo += "Dimensiones material: X%smm Y%smm \n" % (round(x,2),round(y,2))
            textinfo += "Posicion del material: X%smm Y%smm \n" % (round(x_distance,2),round(y_distance,2))
        
        textinfo += "\n" + info + "\n#INFO_DETALLADA:\n" + settings
        self.textsettings = textinfo
        
    def process(self):
        
        if self.savenew and not self.editcycle:
            self.save_settings()
        if self.editcycle and not self.savenew:
            self.name = self.name_input()
            self.get_input()
        if self.editcycle and self.savenew:
            self.save_settings()
            
        self.process_objects()
        self.make_clusters()
        geometry = self.points + self.curves_open + self.curves_inside + self.curves_pocketing + self.curves_outside
        for object in geometry:
            self.previewobjects.append(rs.AddTextDot(str(object.asignedcluster),object.point))
        self.preview_layer()
        self.make_log()
        self.write_registry()
    
    def make_clusters(self):
        
        geometry = self.points + self.curves_open + self.curves_inside + self.curves_pocketing
        
        if self.curves_outside:
            count = 0
            for curve in self.curves_outside:
                edgecurve = rs.ExplodeCurves(curve.curve)
                planar_surface = rs.AddPlanarSrf(curve.curve)
           
                for point in geometry:
                    
                    if point.asignedcluster == -1:
                        uvparam = rs.SurfaceClosestPoint(planar_surface,point.point)
                        closestpoint = rs.EvaluateSurface(planar_surface,uvparam[0],uvparam[1])
                        
                        vector = rs.VectorCreate(point.point,closestpoint)
                        print "vector"
                        print vector[0],vector[1]
                        if rs.ProjectPointToSurface(point.point,planar_surface,(0,0,1)):
                        #if rs.IsPointOnSurface(planar_surface,rs.PointCoordinates(point.point)):
                        #if abs(vector[0]) <= CLUSTER_TOLERANCE and abs(vector[1]) <= CLUSTER_TOLERANCE:
                            
                            #self.previewobjects.append(rs.AddTextDot(str(count),point.point))
                            #self.previewobjects.append(rs.AddTextDot(str(count),rs.CurveStartPoint(curve.curve)))
                            point.asignedcluster = count
                            curve.asignedcluster = count
                            #geometry.pop(geometry.index(point))
                            curve.iscluster = True
                        else:
                            pass
                            #rs.AddLine(point.point,closestpoint)
                        
                count += 1
                rs.DeleteObjects(planar_surface)
                rs.DeleteObjects(edgecurve)
                        
    def make_code(self):
        
        gcode = IN_TEXT
        sec_plane = self.general_input_data[0]
        rapid = self.general_input_data[1]
        start_line = ["G0Z%sF%s" % (sec_plane,rapid)]
        gcode += start_line
        geometry = self.points + self.curves_open + self.curves_inside + self.curves_pocketing
        count = 0
        count_notcluster = 0

        for path in geometry:
            if path.asignedcluster == -1:
                gcode += path.gcode
                count_notcluster += 1
                
        for curve in self.curves_outside:
            if curve.iscluster:
                #self.previewobjects.append(rs.AddTextDot(str(count)+","+str(curve.asignedcluster),rs.CurveStartPoint(curve.curve)))
                for path in geometry:
                    if path.asignedcluster == curve.asignedcluster:
                        #self.previewobjects.append(rs.AddTextDot(str(count)+","+str(path.asignedcluster),rs.CurveStartPoint(path.curve)))
                        gcode+= path.gcode
                    
                gcode += curve.gcode
                count += 1
            else:
                gcode += curve.gcode
                count_notcluster += 1
                
        gcode += OUT_TEXT
        print "Contenedores: %s" % (count)
        print "Cortes individuales: %s" % (count_notcluster)   
        return gcode
    
    def delete_registry(self):
       
        try:
            rs.DeleteDocumentData(REGISTRY_SECTION,self.name)
            return True
        except:
            return False
    
    def write_registry(self):
        
        line = {}
        line[self.name] = self.preset
        self.delete_registry()
        rs.SetDocumentData(REGISTRY_SECTION,self.name,str(line))
        rs.SetDocumentData(REGISTRY_SECTION,"GI",str(self.general_input_data))
        
    def save_settings(self):
        
        line = {}
        nombre = self.name_input()
        line[nombre] = json.dumps(self.preset)
        archivo_rutinas = open(PATH_RUTINAS,"a")
        archivo_rutinas.write(str(line) + "\n")
        archivo_rutinas.close()
        self.name = nombre
    
    def preview_layer(self):
        
        geometry = self.points + self.curves_open + self.curves_inside + self.curves_outside + self.curves_pocketing
        preview = [self.previewobjects]
        
        for i in geometry:
            preview.append(i.preview)
        
        if PREVIEW_LAYER_NAME in rs.LayerNames():
            rs.LayerLocked(PREVIEW_LAYER_NAME,False)
            rs.DeleteObjects(rs.ObjectsByLayer(PREVIEW_LAYER_NAME))
        else:
            rs.AddLayer(PREVIEW_LAYER_NAME, color=0, visible=True, locked=False, parent=None)
        for curve in preview:
            rs.ObjectLayer(curve,PREVIEW_LAYER_NAME)
        
        rs.LayerLocked(PREVIEW_LAYER_NAME,True)
    
    def sort_points(self,curves):
    
        a_curves = []
        curves_center =[] 
        for curve in curves:
            start_pt = rs.PointCoordinates(curve.point)
            curves_center.append((curve,start_pt[0],start_pt[1]))
        a_curves = sorted(curves_center, key = operator.itemgetter(2, 1))
        clean_curves = []
        for curve in a_curves:
            clean_curves.append(curve[0])
        return clean_curves

    def sort_curves_area(self,curves):
        
        a_curves = []
        curves_area =[] 
        for curve in curves:
            area = rs.CurveArea(curve.curve)[0]
            curves_area.append((curve,area))
        a_curves = sorted(curves_area, key = operator.itemgetter(1))
        clean_curves = []
        for curve in a_curves:
            clean_curves.append(curve[0])   
        return clean_curves
    
    def sort_curves(self,curves):
        
        a_curves = []
        curves_center =[] 
        for curve in curves:
            start_pt = rs.CurveStartPoint(curve.curve)
            curves_center.append((curve,start_pt[0],start_pt[1]))
        a_curves = sorted(curves_center, key = operator.itemgetter(2, 1))
        clean_curves = []
        for curve in a_curves:
            clean_curves.append(curve[0])   
        return clean_curves    
    
    
    def process_objects(self):
        
        cpoints = []
        cengraving = []
        ccurvesinside = []
        ccurvesoutside = []
        ccurvespocketing = []
        
        for point in self.points:
            cpoints.append(g_point(point,self.preset["point"],self.general_input_data))
            self.points = self.sort_points(cpoints)
            
        for curve in self.curves_open:
            cengraving.append(g_open_curve(curve,self.preset["engraving"],self.general_input_data))
            self.curves_open = self.sort_curves(cengraving)
            
        for curve in self.curves_pocketing:
            ccurvespocketing.append(g_curve(curve,self.preset["pocketing"],self.general_input_data,-1))
            self.curves_pocketing = self.sort_curves(ccurvespocketing)
            
        for curve in self.curves_inside:
            ccurvesinside.append(g_curve(curve,self.preset["curve"],self.general_input_data,-1))
            self.curves_inside = self.sort_curves(ccurvesinside)
            
        for curve in self.curves_outside:
            ccurvesoutside.append(g_curve(curve,self.preset["curve"],self.general_input_data,1))
            self.curves_outside = self.sort_curves_area(ccurvesoutside)
        
    def get_input(self):
         
    
        spoints = self.point_input()
        self.preset["point"] = list(spoints)
          
    
        scurves = self.pocketing_input()
        self.preset["pocketing"] = list(scurves)
    
        scurvesopen = self.engraving_input()
        self.preset["engraving"] = list(scurvesopen)
          
    
        scurves = self.curve_input()
        self.preset["curve"] = list(scurves)
        
    def point_input(self):
        
        items = POINT_INPUT_VALUES
        input_data = rs.PropertyListBox(items,self.preset["point"],"Barrenos .....","Configuracion de barrenado")
        return input_data
    
    def user_input(self):
        
        
        try:
            spkuser = rs.GetDocumentData(REGISTRY_SECTION,"spkuser")
        except:
            spkuser = ""
        
        input_data = rs.StringBox ("Usuario SPK:",spkuser,"Usuario")
        rs.SetDocumentData(REGISTRY_SECTION,"spkuser",input_data)
        return input_data
    
    
    def write_registry(self):
        
        line = {}
        line[self.name] = self.preset
        self.delete_registry()
        rs.SetDocumentData(REGISTRY_SECTION,self.name,str(line))
        rs.SetDocumentData(REGISTRY_SECTION,"GI",str(self.general_input_data))

    
    def name_input(self):
    
        input_data = rs.StringBox ("Nombre base de datos:",self.name,"Guardar rutina en base de datos")
        return input_data
    
    def pocketing_input(self):
        
        items = CURVE_POCKETING_VALUES
        input_data = rs.PropertyListBox(items, self.preset["pocketing"],"Cajas ||||| ", "Configuracion de corte")
        return  input_data
    
    def curve_input(self):
        
        items = CURVE_INPUT_VALUES
        input_data = rs.PropertyListBox(items, self.preset["curve"],"Curvas -----", "Configuracion de corte")
        return  input_data
        
    def engraving_input(self):
        
        items = ENGRAVING_INPUT_VALUES
        input_data = rs.PropertyListBox (items, self.preset["engraving"],"Grabado ~~.~~","Configuracion de grabado")
        return  input_data

def Main():
    
    objects = colect_objects()
    
    if objects:
        sec_plane = get_sec_plane(objects)
        new_batch = batch(objects,sec_plane)
        new_batch.process()
        gcode = new_batch.make_code()
        file_path =save_file(gcode,new_batch.general_input_data[2])
        image_path,image_path_2 =  save_image(file_path,new_batch.previewobjects)
        settings_path = save_settings_file(file_path,new_batch.textsettings,"Configuracion")
        info_path = save_settings_file(file_path,new_batch.textinfo,"Info")
        if new_batch.upload:
            user = new_batch.user_input()
            upload_to_server(file_path,settings_path,image_path,image_path_2,user,new_batch.price)
    else:
        print "nope"
        ui = SettingsControl(6)
        Rhino.UI.Dialogs.ShowSemiModal(ui.form)
        
if( __name__ == "__main__" ):
    import Meier_UI_Utility
    Main()
