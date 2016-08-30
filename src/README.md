# SPKCAM:.
Es un plugin de Rhino5 que te permite generar codigo-g a través de un código de color y subirlo automáticamente a la nube de SPK:. 
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

La instalación de SPKCAM:. requiere los siguientes programas:
Rhino 5 https://www.rhino3d.com
IronPython http://ironpython.net

Una vez instalado abre Rhino y ejecuta los siguientes comandos:
	Spkcam (Abre la interfaz grafica del generador de codigo-g)
	Spkcam_gcode_preview (Te permite visualizar archivos de codigo-g ya generados)