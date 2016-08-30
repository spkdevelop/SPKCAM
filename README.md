# SPKCAM:.
Es un plugin de Rhino5 que te permite generar codigo-g a través de un código de color y subirlo automáticamente a la nube de SPK:. También cuenta con un sistema de detección de piezas (imagen 3) y una base de datos con velocidades sugeridas de corte según cada material.

###Código Color:

Para asignar el color se debe utilizar la paleta de color de Rhino.
Azul (BLUE, rgb (0,0,255): Compensación externa<br>
Rojo (RED, rgb (255,0,0): Compensación interna<br>
Verde: (GREEN, rgb (0,255,0)Grabado sobre linea<br>
Magenta (MAGENTA, rgb (0,255,255): Caja<br>

###Versión Beta:

Actualmente el proyecto se encuentra en desarrollo por lo que te recomendamos actualizarlo de manera frecuente. No es apto para todo tipo de maquinaria CNC esta enfocado para controladores GRBL como Arduino y TinyG por lo que su eso es responsabilidad del usuario final y no nos hacemos responsables por ningún tipo de daño directo o indirecto que pueda causar el programa.

###Instalación Windows:

La instalación de SPKCAM:. requiere los siguientes programas:<br>
Rhino 5 https://www.rhino3d.com<br>
IronPython http://ironpython.net<br><br>

###Comandos Rhino5:

	Spkcam (Abre la interfaz grafica del generador de codigo-g)<br>
	Spkcam_gcode_preview (Te permite visualizar archivos de codigo-g ya generados)<br>
