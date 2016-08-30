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
# Find us at: http://www.spkautomatizacion.com


import rhinoscriptsyntax as rs
import Rhino
import time
POINT_TOL = .5
ROUND_TOL = 2
color_palette = {"cut":(153,204,255),"plunge":(254,184,0),"point":(153,204,255)}

class g_curve():
    
    def __init__(self,curve,input_data,general_input,compensation,pocketing):
        self.log = []
        self.input_data = input_data
        self.general_input = general_input
        self.compensation = compensation
        self.pocketing = pocketing
        self.asignedcluster = -1
        self.iscluster = False
        self.nurbs_curve  = curve
        self.curve  = curve #Curva original2
        self.type = "point"  if rs.IsPoint(self.nurbs_curve) else "curve" if rs.IsCurveClosed(self.nurbs_curve) else "open_curve" 
        self.point = self.curve if rs.IsPoint(self.nurbs_curve) else rs.CurveAreaCentroid(self.nurbs_curve)[0] if rs.IsCurveClosed(self.nurbs_curve) else rs.CurveStartPoint(self.nurbs_curve)   # Centroide curva original
        self.start_point = rs.PointCoordinates(self.nurbs_curve,False) if rs.IsPoint(self.nurbs_curve) else rs.CurveStartPoint(self.nurbs_curve)
        self.cut_curve = self.get_cut_curve()
        self.time = 10

        
    def round_point(self,point):
        return (round(point[0],ROUND_TOL),round(point[1],ROUND_TOL),round(point[2],ROUND_TOL)) 
    
    def process(self):
        
        if rs.IsPoint(self.nurbs_curve):
            self.preview = self.get_cut_path_point(self.cut_curve)
        elif self.compensation == 0 and not rs.IsCurveClosed(self.nurbs_curve):
            self.preview =  self.get_cut_path_open(self.cut_curve) 
        else:
            self.preview =  self.get_cut_path_closed(self.cut_curve)
            
        self.gcode = self.get_g_code(self.preview)
  
    
    def get_g_code(self,crv_list):

        gcode = []
        if not rs.IsPoint(self.nurbs_curve):
            feed_plunge = self.input_data['feed_plunge']
            feed_rapid = self.general_input["feed_rapid"]
            feed_cut = self.input_data["feed_cut"]
        else:
            feed_plunge = self.input_data['feed']
            feed_rapid = self.input_data["feed"]
            feed_cut = self.input_data["feed"]
        
        #Crea el G0Hello y el primer punto de corte y extrae la primer curva de corte
        hello_pt = self.round_point(rs.CurveStartPoint(crv_list[0]))
        gcode.append("G0X%sY%sZ%sF%s" % (hello_pt[0],hello_pt[1],hello_pt[2],int(feed_rapid)))
        start_cut__pt = self.round_point(rs.CurveEndPoint(crv_list[0]))
        gcode.append("G1Z%sF%s" % (start_cut__pt[2],int(feed_plunge)))
        crv_list = crv_list[1:]
        #revisa cada bloque de curvas 
        last_state = "plunge"
        for crv in crv_list: 
            crv_rgb = (rs.ColorRedValue(rs.ObjectColor(crv)),rs.ColorGreenValue(rs.ObjectColor(crv)),rs.ColorBlueValue(rs.ObjectColor(crv)))
            new_state = "cut" if crv_rgb == color_palette["cut"] else "plunge"  
            add_feed = True if new_state != last_state else False
            last_state = new_state
            curve_segments = rs.ExplodeCurves(crv, delete_input=False)
            if not curve_segments: curve_segments = [rs.CopyObject(crv)]
            #revisa cada segmento en la curva para ver si es arco o linea etc y asigna codigo por punto 
            for crv in curve_segments:
                crv_gcode = []
                if rs.IsLine(crv) or rs.CurveLength(crv)<POINT_TOL:
                    crv_endpt = self.round_point(rs.CurveEndPoint(crv))
                    if curve_segments.index(crv) == 0 and add_feed:  #si hay cambio de estado entre plunge y cut y es primera linea añade la variable de feed
                        actual_feed = feed_cut if new_state == "cut" else feed_plunge
                        crv_gcode.append("X%sY%sZ%sF%s" % (crv_endpt[0],crv_endpt[1],crv_endpt[2],int(actual_feed)))
                    else:
                        crv_gcode.append("X%sY%sZ%s" % (crv_endpt[0],crv_endpt[1],crv_endpt[2]))
                else:
                    no_points = int(rs.CurveLength(crv)/POINT_TOL)
                    pts = rs.DivideCurve(crv,no_points, create_points=False, return_points=True)[1:]
                    for pt in pts:
                        
                        if curve_segments.index(crv) == 0 and pts.index(pt) == 0 and add_feed:  #si hay cambio de estado entre plunge y cut y es primera linea añade la variable de feed
                            pt = self.round_point(pt)
                            actual_feed = feed_cut if new_state == "cut" else feed_plunge
                            crv_gcode.append("X%sY%sZ%sF%s" % (pt[0],pt[1],pt[2],int(actual_feed)))
                        else:
                            pt = self.round_point(pt)
                            crv_gcode.append("X%sY%sZ%s" % (pt[0],pt[1],pt[2]))
                
                gcode += crv_gcode
                rs.DeleteObject(crv)

        return gcode
    
    def get_cut_path_point(self,point):
        o_point = point
        point = rs.PointCoordinates(o_point)
        no_entries = self.input_data["entries"]
        level_depth = self.input_data["depth"]/ no_entries
        sec_plane = self.general_input["sec_plane"]
        #Lista final de operacion de cortador por curva
        curves_cut_path = []
    
        start_point = (point[0],point[1],point[2]+2)
        hello_line = rs.AddLine((point[0],point[1],sec_plane),start_point)
        rs.ObjectColor(hello_line,color_palette["cut"])
        curves_cut_path.append(hello_line)
        
        for entrie in range(1,int(no_entries)+1):
            end_point = (point[0],point[1],entrie*level_depth)
            in_line = rs.AddLine(start_point,end_point)
            out_line = rs.AddLine(end_point,start_point)
            rs.ObjectColor([in_line,out_line],color_palette["cut"])
            curves_cut_path += [in_line,out_line]
            
        end_line = rs.AddLine(start_point,(point[0],point[1],sec_plane))
        rs.ObjectColor(end_line,color_palette["cut"])
        curves_cut_path.append(end_line)
        rs.DeleteObject(o_point)
        return curves_cut_path
             
    def get_cut_path_open(self,crv):
        
        no_entries = self.input_data["entries"]
        level_depth = self.input_data["depth"]/ no_entries
        sec_plane = self.general_input["sec_plane"]
        #Lista final de operacion de cortador por curva
        curves_cut_path = [] 
        
        for entrie in range(1,int(no_entries)+1):
 
            translation = rs.VectorAdd((0,0,0),(0,0,level_depth*entrie))
            level_curve = rs.CopyObject(crv,translation)
            rs.ObjectColor(level_curve,color_palette["cut"])
            if entrie % 2 == 0: rs.ReverseCurve(level_curve)
            if entrie == 1:
                entry_end_point = rs.CurveStartPoint(level_curve)
                in_curve = rs.AddLine((entry_end_point[0],entry_end_point[1],sec_plane),entry_end_point)
                rs.ObjectColor(in_curve,color_palette["plunge"])
                curves_cut_path.append(in_curve)
            
            curves_cut_path.append(level_curve)
            
            if entrie < no_entries:
                level_ept = rs.CurveEndPoint(level_curve)
                plunge_curve = rs.AddLine(level_ept,(level_ept[0],level_ept[1],(entrie+1)*level_depth))
                rs.ObjectColor(plunge_curve,color_palette["plunge"])
                curves_cut_path.append(plunge_curve)
            
            
        final_point = rs.CurveEndPoint(level_curve)
        out_curve = rs.AddLine(final_point,(final_point[0],final_point[1],sec_plane))
        rs.ObjectColor(out_curve,color_palette["cut"])
        curves_cut_path.append(out_curve)
        
        rs.DeleteObjects([crv])
        
        return curves_cut_path
   
    def isCurveNew(self,offsets,curve):
        if offsets:
            for offset in offsets:
                if rs.Distance(rs.CurveStartPoint(offset),rs.CurveStartPoint(curve))==0:
                    return False
        return True
    
    def getSmall(self,curve_1,curve_2):
        if self.isSmall(curve_1, curve_2):
            return curve_1
        else:
            return curve_2    
    
    def isSmall(self,curve_1,curve_2):
        if rs.CurveArea(curve_1) < rs.CurveArea(curve_2):
            return  True
        else:
            return False
    
    def OffsetCurve(self,level_cut):
        
        check_presision = 10
        offset_type=1
        branched_curves = []
        main_curve = level_cut
        offset_distance = self.general_input["cut_diam"] * self.input_data["xy_dist"]
        curve_1 = rs.OffsetCurve(main_curve,rs.CurveAreaCentroid(main_curve)[0],-.1,None,offset_type)
        curve_2 = rs.OffsetCurve(main_curve,rs.CurveAreaCentroid(main_curve)[0],.1,None,offset_type)
        
        if curve_1 and curve_2:
            if len(curve_1) != 1 or len(curve_2) != 1:
                rs.DeleteObjects(curve_1)
                rs.DeleteObjects(curve_2)
                return branched_curves
            
        mini_test = self.getSmall(curve_1, curve_2)
        do_points = rs.DivideCurve(mini_test,check_presision,False)
        rs.DeleteObjects([curve_1,curve_2])
        do_points.append(rs.CurveAreaCentroid(main_curve)[0])
        
        for i in range(0,len(do_points)):
            new_offset_curve = rs.OffsetCurve(main_curve,do_points[i],offset_distance,None,offset_type)
            try:
                if self.isCurveNew(branched_curves, new_offset_curve) and rs.IsCurveClosed(new_offset_curve) and self.isSmall(new_offset_curve, main_curve):
                    branched_curves.append(new_offset_curve)
                else:
                    rs.DeleteObject(new_offset_curve)
            except:
                if new_offset_curve:
                    rs.DeleteObjects(new_offset_curve)        
        
        for curve in branched_curves:
            rs.ObjectColor(curve,color_palette["cut"])
            
        if not branched_curves or len(branched_curves) > 1:
            
            branched_curves.append("sec_plane")
            
        return branched_curves
    
    def make_pocket_curves(self,level_cut):
        
        cut_curves = []
        offset_curves = self.OffsetCurve(level_cut)
        if offset_curves:
            for offset_curve in offset_curves:
                cut_curves.append(offset_curve)
                if offset_curve != "sec_plane":
                    deep_curve = self.make_pocket_curves(offset_curve)
                    if deep_curve:
                        cut_curves += deep_curve
            
            return cut_curves
        else:
            return False
    
    def finish_pocket_curves(self,crv_list):
        
        block_curves = []
        for i in range(0,len(crv_list)):
            if i == 0:
                pep = rs.CurveEndPoint(self.cut_curve)
                csp = rs.CurveStartPoint(crv_list[i])
                join_line = rs.AddLine(pep,csp)
                rs.ObjectColor(join_line,color_palette["cut"])
                block_curves.append(join_line)
                
            crv = crv_list[i]
            if crv == "sec_plane":
                block_curves.append(crv)
            else:
                try:
                    if i<len(crv_list) and crv_list[i+1] != "sec_plane":
                        nsp = rs.CurveStartPoint(crv_list[i+1])
                        cep = rs.CurveEndPoint(crv_list[i])
                        join_line = rs.AddLine(cep,nsp)
                        rs.ObjectColor(join_line,color_palette["cut"])
                        block_curves.append(crv_list[i])
                        block_curves.append(join_line)
                    else:
                        block_curves.append(crv)
                except:
                    pass
        return block_curves
                                      
    def get_cut_path_closed(self,crv):
        
        #crea la curva de corte y la curva de plunge en el nivel original
        plunge_distance = self.input_data["plunge"] if self.compensation != 0 else 10.0
        no_entries = self.input_data["entries"]
        level_depth = self.input_data["depth"]/ no_entries
        crv_domain = rs.CurveDomain(crv)
        crv_length = rs.CurveLength(crv)
        if plunge_distance >= crv_length: plunge_distance = crv_length*.8
        crv_domain_param = crv_domain[1]-crv_domain[0]
        trim_domain =  (plunge_distance*crv_domain_param)/crv_length
        planar_plunge_crv,cut_crv = rs.SplitCurve(rs.CopyObject(crv),rs.CurveDomain(crv)[0]+trim_domain)
        no_points = int(rs.CurveLength(planar_plunge_crv)/POINT_TOL)
        plunge_pts = rs.DivideCurve(planar_plunge_crv,no_points, create_points=False, return_points=True)
        plunge_moved_pts = []
        z_count = abs(level_depth)
        z_pass = abs(level_depth/no_points)
        for pt in plunge_pts:
            new_point = pt[0],pt[1],pt[2]+z_count
            plunge_moved_pts.append(new_point)
            z_count -= z_pass
            
        plunge_crv = rs.AddPolyline(plunge_moved_pts)
        rs.SimplifyCurve(plunge_crv)
        
        #Crea la curva de corte para pocketing si se requiere
        pocketing_crv = None if not self.pocketing else self.finish_pocket_curves(self.make_pocket_curves(crv))
        #Lista final de operacion de cortador por curva
        curves_cut_path = [] 
        #agrega la entrada del cortador
        
        entry_end_point = rs.CurveStartPoint(planar_plunge_crv)
        sec_plane = self.general_input["sec_plane"]
        in_curve = rs.AddLine((entry_end_point[0],entry_end_point[1],sec_plane),entry_end_point)
        rs.ObjectColor(in_curve,color_palette["plunge"])
        curves_cut_path.append(in_curve)
        #general la lista de curvas y las ordena por nivel diferenciando entre plunge y corte por color
        for entrie in range(1,int(no_entries)+1):
            z_level = level_depth*entrie
            translation = rs.VectorAdd((0,0,0),(0,0,z_level))
            level_plunge= rs.CopyObject(plunge_crv,translation)
            level_cut = rs.CopyObject(cut_crv,translation)
            rs.ObjectColor(level_plunge,color_palette["plunge"])
            rs.ObjectColor(level_cut,color_palette["cut"])
            curves_cut_path.append(level_plunge)
            curves_cut_path.append(level_cut)
            if self.pocketing:
                pocketing_curves = self.get_pocket_entry(z_level,translation,pocketing_crv)
                curves_cut_path += pocketing_curves
        #agrega la ultima linea de corte como plunge para no generar bote de pieza tan brusco
        final_cut = rs.CopyObject(planar_plunge_crv,translation)
        rs.ObjectColor(final_cut,color_palette["plunge"])
        curves_cut_path.append(final_cut)
        #agrega la salida del cortador
        final_point = rs.CurveEndPoint(final_cut)
        out_curve = rs.AddLine(final_point,(final_point[0],final_point[1],sec_plane))
        rs.ObjectColor(out_curve,color_palette["cut"])
        curves_cut_path.append(out_curve)
        
        rs.DeleteObjects([planar_plunge_crv,plunge_crv,cut_crv,crv])
        
        if self.pocketing:
            for po_crv in pocketing_crv:
                if po_crv != "sec_plane":
                    rs.DeleteObject(po_crv)
        
        return curves_cut_path
    
    def get_pocket_entry(self,z_level,translation,pocket_list):
        
        revised_list = []
        last_obj = None
        for obj in pocket_list:
            if obj != "sec_plane":
                revised_list.append(rs.CopyObject(obj,translation))
            else:
                if last_obj != obj:
                    revised_list.append(obj)
            last_obj = obj
        pocket_list = revised_list
        for i in range(0,len(pocket_list)):
            crv = pocket_list[i]
            if crv == "sec_plane": #Cambio intermedio
                pep = rs.CurveEndPoint(pocket_list[i-1])
                try:
                    nsp = rs.CurveStartPoint(pocket_list[i+1])
                except:
                    
                    npt = rs.CurveStartPoint(self.cut_curve)
                    nsp = (npt[0],npt[1],z_level)
                   
                points = [rs.CurveEndPoint(pocket_list[i-1]),(pep[0],pep[1],self.general_input["sec_plane"]),(nsp[0],nsp[1],self.general_input["sec_plane"]),nsp]
                travel_line = rs.AddPolyline(points)
                rs.ObjectColor(travel_line,color_palette["cut"])
                pocket_list[i] = travel_line
                        
        return pocket_list
            
    def find_point_in_curve(self,crv):
        offset_points = rs.BoundingBox(crv)
        diagonal = rs.AddLine(offset_points[0],offset_points[2])
        test_points = rs.DivideCurveLength(diagonal,POINT_TOL,create_points=False, return_points=True)
        rs.DeleteObject(diagonal)
        for point in test_points:
            if rs.PointInPlanarClosedCurve(point,crv):
                return point
        return self.point
    
    def get_cut_curve(self):
        
        if self.compensation == 0: return rs.CopyObject(self.nurbs_curve)
        
        offset_distance = self.general_input["cut_diam"] * 0.5

        scl_obj = rs.ScaleObject(self.nurbs_curve,self.point,(1.2,1.2,1),True)
        offset_points = rs.BoundingBox(scl_obj)
        rs.DeleteObject(scl_obj)

        offset_point_a = offset_points[0]
        offset_point_b = self.point
        if not rs.PointInPlanarClosedCurve(self.point,self.nurbs_curve): offset_point_b = self.find_point_in_curve(self.nurbs_curve)
        offset_a = rs.OffsetCurve(self.nurbs_curve,offset_point_a,offset_distance,None,2)
        offset_b = rs.OffsetCurve(self.nurbs_curve,offset_point_b,offset_distance,None,2)

        #Revisa si el offset no genero curvas separadas y si es el caso asigna la curva original como offset comparativo
        if not offset_a or len(offset_a) != 1:
            self.log.append("offset error: el cortador no cabe en una de las curvas, se reemplazo con la curva original.")
            if offset_a: rs.DeleteObjects(offset_a)
            offset_a = rs.CopyObject(self.nurbs_curve)
            
        if not offset_b or len(offset_b) != 1:
            self.log.append("offset error: el cortador no cabe en una de las curvas, se reemplazo con la curva original.")
            if offset_b: rs.DeleteObjects(offset_b)  
            offset_b = rs.CopyObject(self.nurbs_curve)
                
        #Revisa el area para saber cual es el offset interno o externo
        if rs.CurveArea(offset_a) < rs.CurveArea(offset_b):
            in_offset = offset_a
            out_offset = offset_b
        else:
            in_offset = offset_b
            out_offset = offset_a
        #Responde dependiendo que compensacion se necesita
        if self.compensation == 1:
            rs.DeleteObject(in_offset)
            return out_offset
        elif self.compensation == -1:
            rs.DeleteObject(out_offset)
            return in_offset
        else:
            rs.DeleteObject(in_offset)
            rs.DeleteObject(out_offset)
            return None
        

def main():
    
    input_data = {'feed_cut': 1600.0, 'cero_pass': 0.0, 'feed_plunge': 1200.0, 'depth': -10.0, 'entries': 3.0, 'plunge': 130.0, 'aproach_dist': 3.0}
    pocketing_data = {'plunge': 10.0, 'feed_cut': 1600.0, 'xy_dist': 0.65000000000000002, 'aproach_dist': 3.0, 'feed_plunge': 1200.0, 'entries': 3.0, 'cero_pass': 0.0, 'depth': -6.0}

    general_input = {'feed_rapid': 3000.0, 'sec_plane': 6.0, 'cut_diam': 6.0}
    
    obj = rs.GetObjects("Selecciona curvas:")
    for crv in obj:
        g_curve(crv,pocketing_data,general_input,-1,True).process()
  
        
if __name__=="__main__":
    main()