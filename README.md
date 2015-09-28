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

###Instalación Windows:

Para instalar el SPKCAM:. es necesario contar con Rhino5 SR9 o superior. Basta con descomprimir el archivo ZIP y ejecutar el comando _RunPythonScript en Rhino yseleccionar el archivo SPKCAM.py que acabamos de descomprimir. Para habilitar la función de "subir a la nube" es necesario seguir estos pasos:<br>

1. Descarga la carpeta ZIP de <a href="https://www.python.org/ftp/python/2.7.10/python-2.7.10.amd64.msi"> SPKCAM:. </a>.<br>
2. Descomprime la carpeta en algun lugar seguro. Ej. "C:\Program Files\Rhinoceros 5 (64-bit)\Plug-ins\SPKCAM"<br>
3. Desacargar la ultima versión de <a href="https://www.python.org/ftp/python/2.7.10/python-2.7.10.amd64.msi"> Python 2.7 </a><br>
4. Durante la instalación selecciona las opciónes: añadir PYTHONPATH to WINDOWSPATH y instalar "pip"<br>
5. Reinicia tu computadora.<br>
6. Abre Rhino 5 y ve a tools/options/aliases "add new alias"<br>
7. Crea un nuevo alias con el nombre "SPKCAM" y el comando<br>
  "-_RunPythonScript ("C:\Program Files\Rhinoceros 5 (64-bit)\Plug-ins\SPKCAM\SPKCAM.py")"<br>
Reemplaza la ruta del archivo con tu información.<br>
8. Una vez creado el alias podrás escribir el comando SPKCAM en la pantalla de rhino y la aparece la interfaz de usuario.<br>

