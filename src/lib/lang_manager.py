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

VARIABLE_NAMES = {
                  
            "material_info":[
            "mat",
            "dim_x",
            "dim_y",
            "dim_z",
            "no_filos",
            "tipo_filos",
            "notas"],
                  
            "barrenado":
            ["feed",
            "depth",
            "entries"],
            
"corte":[
            "depth",
            "entries",
            "plunge",
            "feed_cut",
            "feed_plunge"],

"desbaste":[
            "depth",
            "entries",
            "xy_dist",
            "plunge",
            "feed_cut",
            "feed_plunge"],
    
"grabado":[
            "depth",
            "entries",
            "feed_cut",
            "feed_plunge"],
                }

INPUT_VALUES_ES = {"material_info":[
            "Material:",
            "Dimension en Xmm:",
            "Dimension en Ymm:",
            "Altura material en Zmm:",
            "Numero de filos cortador:",
            "Tipo de filos",
            "Notas:"],
                
            "barrenado":[
            "Feed mm/min:",
            "Profundidad barreno (Negativo):",
            "Numero pasadas"],
            
"corte":[
            "Profundidad corte (Negativo):",
            "Numero de pasadas:",
            "Plunge mm lineales:",
            "Feed mm/min:",
            "Plunge mm/min:"],

"desbaste":[
            "Profundidad corte (Negativo):",
            "Numero de pasadas en Z:",
            "% del diametro entre pasadas (0-1):",
            "Plunge mm lineales:",
            "Feed mm/min:",
            "Plunge mm/min:"],
    
"grabado":["Profundidad corte (Negativo):",
            "Numero de pasadas:",
            "Feed mm/min:",
            "Plunge mm/min:"]
                }

INPUT_VALUES_EN = {"material_info":[
            "Material:",
            "Xmm Dimension:",
            "Ymm Dimension:",
            "Zmm Material Height:",
            "Number of flutes:",
            "Flute shape:",
            "Notes:"],
                
            "barrenado":[
            "Drill feed mm/min:",
            "Drill distance (Negative int):",
            "Number of entries:"],
            
"corte":[
            "Cut depth (Negative int):",
            "Number of entries:",
            "Plunge horizontal dist:",
            "Cut feed mm/min:",
            "Plunge feed mm/min:"],

"desbaste":[
            "Box depth (Negative int):",
            "Number of entries:",
            "Step dist (Float percent 0.0-1.0):",
            "Plunge horizontal dist:",
            "Cut feed mm/min:",
            "Plunge feed mm/min:"],
    
"grabado":[
            "Engraving depth (Negative int):",
            "Number of entries:",
            "Cut feed mm/min:",
            "Plunge feed mm/min:"]
                }

UITXT_ES = {
           "terms":"¿Aceptas los terminos y condiciones?",
           "login":"No hay login",
           "sel_r":"Seleccionar rutina",
           "sel_r_no":"No hay rutina seleccionada",
           "nr":"Nueva rutina",
           "ed":"Editar",
           "mo":"Mostrar",
           "bo":"Borrar",
           "diam":"Diametro del cortador: ",
           "autocluster":"Autodeteccion de piezas",
           "sec":"Plano de seguridad:    ",
           "xy":"Ordenar Zig-Zag",
           "mr":"Movimiento rapido:      ",
           "dist":"Ordenar cercania",
           "code":"Generara codigo",
           "gt":"Nube",
           "nube":"Subir a la nube",
           "pc":"Guardar en PC",
           "init":"Inicio de consola",
           "lfo":"Login encontrado",
           "abrexp":"Abriendo explorador",
           "loproc":"Login en proceso...revisa tu explorador.",
           "looutproc":"Logout en proceso...",
           "tmpex":"Tiempo excedido... Login fallo.",
           "error_wait":"Espera, generando codigo",
           "error_generate":"Genera un codigo antes de guardar.",
           "error_input":"Falta nombre de producto o url",
           "uploading":"Subiendo codigo al servidor...",
           "save_file":"Selecciona donde guardar el codigo",
           "error_login":"No se pudo subir el codigo a la nube. Falta Login.",
           "new_product":"Se creo un producto nuevo en la nube",
           "error_coneccion":"Error de conexion",
           "time_txt":"Tiempo de corte",
           "file_saved":"Archivo guardado",
           "conf":"Configuracion",
           "del":"Eliminado",
           "name":"Nombre:",
           "nueva":"Nueva rutina",
           "save_pers":"Guardar la rutina en la base de datos persistente? \n\nSi selecciona No la rutina se guardara unicamente en este archivo de Rhino.",
           "database":"Base de datos",
           "selobj":"Selecciona los objetos",
           "seldesc":"Selecciona curvas y puntos:",
           "selobj_res":"Objetos seleccionados",
           "selobj_res_no":"No hay objectos seleccionados",
           "gencode":"Generando codigo...",
           "gencodeok":"Codigo generado",
           "init":"Iniciando Spkcam...",
           "selobjbutton":"Selecciona curvas",
           "cutconf":"Configuracion de corte",
           "bye":"Spkcam cerrado."
           }

UITXT_EN = {
           "terms":"Click yes to accept terms and conditions",
           "login":"No login found",
           "sel_r":"Select cut preset",
           "sel_r_no":"No selected cut preset",
           "nr":"New cut preset",
           "ed":"Edit",
           "mo":"Show",
           "bo":"Delete",
           "diam":"Drill diameter:         ",
           "autocluster":"Autodetect objects",
           "sec":"Security plane:       ",
           "xy":"Sort Zig-Zag",
           "mr":"Feed rapid:            ",
           "dist":"Sort closest",
           "code":"Generate code",
           "gt":"Cloud",
           "nube":"Upload to cloud",
           "pc":"Save in PC",
           "init":"Console initiated",
           "lfo":"Login found",
           "abrexp":"Opening browser",
           "loproc":"Login in process, check your browser",
           "looutproc":"Logout in process....",
           "tmpex":"Login failed: waiting time exceeded",
           "error_wait":"Wait until de code is generated",
           "error_generate":"Generate code before saving",
           "error_input":"Insert product's name or url address.",
           "uploading":"Uploading code to server",
           "save_file":"Save path",
           "error_login":"Upload error: Please sign in.",
           "new_product":"New cloud product created",
           "error_coneccion":"Connection error",
           "time_txt":"Cut time",
           "file_saved":"File saved",
           "conf":"Settings",
           "del":"Deleted",
           "name":"Name:",
           "nueva":"New cut preset",
           "save_pers":"Save cut preset inside this Rhino file only? \n\nIf no is selected, the cut preset will appear in every file",
           "database":"Database",
           "selobj":"Select objects",
           "seldesc":"Select curves and points:",
           "selobj_res":"Selected objects",
           "selobj_res_no":"No selected objects",
           "gencode":"Generating code...",
           "gencodeok":"Code generated",
           "init":"Initiating Spkcam...",
           "selobjbutton":"Select objects",
           "cutconf":"Cut preset settings:",
           "bye":"closing spkcam"
           }

def get_variable_names():
    return VARIABLE_NAMES

def get_ui_text(lang):
    
    if lang == "es":
        return UITXT_ES
    elif lang == "en":
        return UITXT_EN
    else:
        return False

def get_input_values(lang):
    if lang == "es":
        return INPUT_VALUES_ES
    elif lang == "en":
        return INPUT_VALUES_EN
    else:
        return False