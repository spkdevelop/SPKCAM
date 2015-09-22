#!/usr/bin/env python
#
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
#
#
# Find us at http://www.spkautomatizacion.com

import requests
import sys

script_password="3VERyuNQwfeJtzX"
base_url="https://spkcloud.appspot.com/get_file_upload_url_super_secret_link-no-one-allowed"

def upload_to_server(save_path,desc_path,images,user,price,pid,name,gname):
    
    settings = ""
    with open(desc_path) as fp:
            for line in fp:
                settings += line
    fp.close()
    technical,contrato = settings.split("#")
    if name != "False":
        file_name = name
    else: 
        file_name = save_path.split("\\")[-1]
    print "SPKCAM:. Uploader" 
    archivo = save_path
    if user.endswith("spkautomatizacion.com"):
        price = str(price)
    else:
        price = "0"
    if pid == "False":
	url=requests.post(base_url,data={"script_password":script_password}).text.strip()
        data={
        "script_password":script_password,
        "nombre": file_name,
        "price":price,
        "new_gcodes_number":"1",
        "contrato":contrato,
        "description": "SPKCAM:. Uploader",
        "labels":"SPKCAM,temporal,upload".strip(),
        "author":user,
        "technical_description_new_0":technical,
        "stars":"1",
        "g_code_name_new_0":gname,
        }
        files=[("new_gcode_file_0",open(archivo)),("files",open(images[0],"rb")),("files",open(images[1],"rb"))]
    else:
	url=requests.post(base_url,data={"script_password":script_password,"pid":pid,"author":user}).text.strip()
        data={
        "script_password":script_password,
        "new_gcodes_number":"1",
        "author":user,
        "technical_description_new_0":technical,
        "g_code_name_new_0":gname,
        "pid": pid,
        }
        files=[("new_gcode_file_0",open(archivo)),("files",open(images[0],"rb")),("files",open(images[1],"rb"))]
    
    print "Subiendo archivos al servidor..."
    requests.post(url, files=files,data=data)
    print "Archivo listo"
    
if __name__=='__main__':
    sys.exit(upload_to_server(sys.argv[1],sys.argv[2],[sys.argv[3],sys.argv[4]],sys.argv[5],sys.argv[6],sys.argv[7],sys.argv[8],sys.argv[9]))
