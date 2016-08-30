#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rhinoscriptsyntax as rs
import Rhino
import os
color_palette = {"cut":(153,204,255),"plunge":(254,184,0),"point":(153,204,255)}
LAYER_NAME = "vector_from_gcode"

def parse_line(line):
    
    line = line.lower().replace("\n","")
    point = []
    
    if line.startswith("(") or line.startswith("m"):
        return point
    
    try:
        if line.find("x") != -1:
            point.append(float(line.split("x")[1].split("y")[0]))
            point.append(float(line.split("y")[1].split("z")[0]))
            if line.find("f") != -1:
                z_pt,feed = line.split("y")[1].split("z")[1].split("f")
                point.append(float(z_pt))
                point.append(int(feed))
            else:
                point.append(float(line.split("y")[1].split("z")[1]))
                        
    except:
        return None
    
    return point

def vector_sum(lines,preview=False):
    
    vector_list = []
    total_time = 0
    total_length = 0
    last_feed = 0
    for i in range(len(lines)):
        point_a = lines[i][:3]
        if i == len(lines)-1: break
        point_b = lines[i+1][:3]
        vector = rs.AddLine(point_a,point_b) if preview else rs.VectorCreate(point_a,point_b)
        if preview: 
            rs.ObjectLayer(vector,LAYER_NAME)
            rs.ObjectColor(vector,color_palette["cut"])
        vector_list.append(vector)
        if len(lines[i]) == 4:
            feed = lines[i][-1]
            last_feed = feed
        
        vector_length =  rs.CurveLength(vector) if preview else rs.VectorLength(vector)
        total_length += vector_length
        total_time += (vector_length)/last_feed 
    
    return vector_list,round(total_time,2),round(total_length,2)
   
    
def vectors_from_gcode(lines,preview=False,only_time=False):
   
    parsed_lines = []
    for line in lines:
        parsed_line = parse_line(line)
        if parsed_line: parsed_lines.append(parsed_line)
        
    vector_list,total_time,total_length = vector_sum(parsed_lines,preview)
    
    if only_time:
        return total_time 
    else: return vector_list,total_time,total_length
    
def main():
    
    print "Spkcam's vector from gcode"
    print "selecciona tu archivo de codifo g:"
    if not rs.IsLayer(LAYER_NAME):
        rs.AddLayer(LAYER_NAME)
    else:
        rs.LayerLocked(LAYER_NAME, locked=False)
    f_path = rs.OpenFileName(title="Selecciona CodigoG", filter=None, folder=None, filename=None, extension=None)
    f = open(f_path)
    gcode = f.readlines()
    f.close()
    vector_list,total_time,total_length = vectors_from_gcode(gcode,True)
    print "Tiempo de corte: %s minutos" % total_time
    print "Logitud total: %s mm" % total_length
    rs.LayerLocked(LAYER_NAME, locked=True)
    
if __name__=="__main__":
    main()