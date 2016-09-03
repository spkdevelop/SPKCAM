# SPKCAM:.
<p>Es un plugin de Rhino5 que te permite generar codigo-g. Funciona con curvas en 2D y puntos. Para asignar la compensación de la herramienta a cada curva se debe cambiar el color del objeto (no del layer) según el código de color de SPK.</p>

###Código Color:

 Para asignar el color se debe utilizar la paleta de Rhino.<br><br>
 Azul (BLUE, rgb (0,0,255): Compensación externa<br>
 Rojo (RED, rgb (255,0,0): Compensación interna<br>
 Verde: (GREEN, rgb (0,255,0): Grabado sobre linea<br>
 Magenta (MAGENTA, rgb (0,255,255): Caja <br>

###Nueva versión:
<p>-Sube directamente los archivos a la nube de SPK desde Rhino.<br>
-Autodetección de piezas.<br>
-Orden de corte por distancia.<br>
-Base de datos actualizada.<br></p>

###Instalación Windows:

<a href="https://github.com/utitankaspk/SPKCAM/raw/master/Spkcam_v1.6.29.08.2016_for_Rhino5.0_Win64-32_Installer.rhi">Descarga el nuevo instalador para Windows 64 y 32bits </a><br>

La instalación de SPKCAM:. requiere los siguientes programas:<br>
-Rhino 5 https://www.rhino3d.com<br>
-IronPython http://ironpython.net (Actualizarlo resuelve problemas de login en win10) <br><br>
<b>NOTA:</b> Algunos SRL de Rhino no son compatibles con IronPython2.7.6. Instalar la <a href="https://drive.google.com/file/d/0B02fjLQVN51aT1BSc21pTUNyaFE/view?usp=sharing" target="_blank">versión 2.7.5</a> resuelve el problema. (Verifica que puedas correr "RunPythonScript" en la consola de Rhino)<br> 

###Comandos Rhino5:

	Spkcam #(Abre la interfaz grafica del generador de codigo-g)
	Spkcam_gcode_preview #(Te permite visualizar archivos de codigo-g ya generados)
	
###Versión Beta:

Actualmente el proyecto se encuentra en desarrollo por lo que te recomendamos actualizarlo de manera frecuente. No es apto para todo tipo de maquinaria CNC. Esta enfocado para controladores GRBL como Arduino y TinyG por lo que su uso es responsabilidad del usuario final y no nos hacemos responsables por ningún tipo de daño directo o indirecto que pueda causar el programa.

