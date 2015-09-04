import requests
import sys

script_password="3VERyuNQwfeJtzX"
base_url="https://spkcloud.appspot.com/get_file_upload_url_super_secret_link-no-one-allowed"

def upload_to_server(save_path,desc_path,images,user,price):
    
    settings = ""
    with open(desc_path) as fp:
            for line in fp:
                settings += line
    fp.close()
    technical,contrato = settings.split("#")
    file_name = save_path.split("\\")[-1]
    print "SPKCAM:. Uploader" 
    url=requests.post(base_url,data={"script_password":script_password}).text.strip()
    archivo = save_path
    if user.endswith("spkautomatizacion.com"):
        price = str(price)
    else:
        price = "0"
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
    "g_code_name_new_0":file_name,
    }
    files=[("new_gcode_file_0",open(archivo)),("files",open(images[0],"rb")),("files",open(images[1],"rb"))]
    print "Subiendo archivos al servidor..."
    requests.post(url, files=files,data=data)
    print "Archivo listo"
    
if __name__=='__main__':
    sys.exit(upload_to_server(sys.argv[1],sys.argv[2],[sys.argv[3],sys.argv[4]],sys.argv[5],sys.argv[6]))
