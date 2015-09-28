# SPKCAM:.
Plugin de Rhino5 que te permite generar codigo-g a través de un código de color y subirlo automáticamente a la nube de SPK:. 
Funciona a través de un código de color que se asigna a cada curva, lo que te permite preparar archivos para corte rápidamente (imagen 2). También cuenta con un sistema de detección de piezas (imagen 3) y una base de datos con velocidades sugeridas de corte según cada material.

###Código Color:
Azul: Compensación externa<br>
Rojo: Compensación interna<br>
Verde: Grabado sobre linea<br>
Magenta: Caja<br>
Cyan: Perímetro del material<br>

###Versión Beta:

Actualmente el proyecto se encuentra en desarrollo por lo que te recomendamos actualizarlo de manera frecuente. Esta es una versión no apta al público en general pero te damos la bienvenida a probarlo bajo tu propia responsabilidad.

###Instalación:
Actualmente solo funciona en Windows. 

Para hacer funcionar el plugin de SPKCAM es necesario contar una versión de Rhino5 con paquete SR9 o superior. Basta con descomprimir el archivo ZIP y ejecutar el comando _RunPythonScript en Rhino y seleccionar el archivo SPKCAM.py en la carpeta recien descomprimida. Es probable que la funcion de "subir a la nube" marque un error, esto quiere decir que hace falta instalar Python 2.7 en tu computadora. 



Para hacer una instalación persistente de SPKCAM:. en tu Rhino es necesario seguir estos pasos:
1. Descarga la carpeta ZIP de <a href="https://www.python.org/ftp/python/2.7.10/python-2.7.10.amd64.msi"> SPKCAM:. </a>.
2. Descomprime la carpeta en algun lugar seguro. Ej. "C://Program Files/Rhino5 64 bits/Plugins/SPKCAM"
3. Desacargar la ultima version de <a href="https://www.python.org/ftp/python/2.7.10/python-2.7.10.amd64.msi"> Python 2.7 </a>
4. Durante la instalación seleccionada la opcion de añadir PYTHONPATH to WINDOWSPATH al igual que instalar "pip"
5. Reinicia tu computadora.
6. Abre Rhino 5 y ve a tools/options/aliases "add new alias"
7. Crea un nuevo alias con el nombre "SPKCAM" y el comando "-_RunPythonScript ("C:Tu usuario/")"
8. Una vez creado el alias podrás escribir el comando SPKCAM en la pantalla de rhino y la aparece la interfaz de usuario.

