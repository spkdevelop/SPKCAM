# SPKCAM:.
Es un plugin de Rhino5 que te permite generar codigo-g con dibujos 2D a través de un código de color que se asigna a cada curva segun la compensación de la herramienta deseada. Puedes subir directamente tus archivos  a la nube de SPK:. para enviarlos a corte con el plugin de SPKClient. También cuenta con un sistema de detección de piezas y una base de datos con velocidades sugeridas de corte según cada material.

###Código Color:

 Para asignar el color se debe utilizar la paleta de color de Rhino.<br><br>
 Azul (BLUE, rgb (0,0,255): Compensación externa<br>
 Rojo (RED, rgb (255,0,0): Compensación interna<br>
 Verde: (GREEN, rgb (0,255,0): Grabado sobre linea<br>
 Magenta (MAGENTA, rgb (0,255,255): Caja <br>

###Versión Beta:

Actualmente el proyecto se encuentra en desarrollo por lo que te recomendamos actualizarlo de manera frecuente. No es apto para todo tipo de maquinaria CNC. Esta enfocado para controladores GRBL como Arduino y TinyG por lo que su uso es responsabilidad del usuario final y no nos hacemos responsables por ningún tipo de daño directo o indirecto que pueda causar el programa.

###Instalación Windows:

<a href="https://github.com/utitankaspk/SPKCAM/raw/master/Spkcam_v1.6.29.08.2016_for_Rhino5.0_Win64-32_Installer.rhi">Descarga el nuevo instalador para Windows 64 y 32bits </a><br>

La instalación de SPKCAM:. requiere los siguientes programas:<br>
Rhino 5 https://www.rhino3d.com<br>
IronPython http://ironpython.net (Actualizarlo resuelve problemas de login en win10) <br>

###Comandos Rhino5:

	Spkcam #(Abre la interfaz grafica del generador de codigo-g)
	Spkcam_gcode_preview #(Te permite visualizar archivos de codigo-g ya generados)
