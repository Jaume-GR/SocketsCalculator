# SocketCalculator

Para la comunicación entre cliente y servidor se ha decidido usar un socket TCP, más concretamente se ha usado el *ThreadingTCPServer* para 
permitir atender múltiples peticiones en el servidor. Se ha elegido TCP frente a UDP porque el servicio necesita intercambiar peticiones y 
respuestas de forma fiable y ordenada. TCP incorpora mecanismos internos de detección de perdidas, retransmisión, etc... los cuales evitan 
que tengamos que implementarlos nosotros en la aplicación como sucedería si usaramos UDP. Si bien TCP resulta más lento que UDP por el 
overhead que suponen dichos mecanismos, para el fin de la aplicación la rapidez que nos ofrece TCP nos es suficiente.


## Cliente.py
El script *cliente.py* se encarga de ejecutar el experimento, a partir de unos parámetros que podemos configurar (ubicados al inicio del código)
se ejecuta el lanzamiento de N hilos, cada uno representando un cliente distinto. Cada cliente, siguiendo una distribución exponencial configurable,
mandará peticiones al servidor. Cada petición constituye una solicitud de realizar una operación, la cual viene a su vez conformada por un operador
y sus argumentos.

Las instrucciones que se envian al servidor siguen una notación prefija, es decir siguen el formato:<br>
``` operación arg1 arg2 ... argn```<br>
siendo *n* el límite establecido para esa operación.

Las operaciones se escogen aleatoriamente de entre las disponibles, a estas se adjunta una cantidad aleatoria de argumentos, 
esto es principalmente para generar tanto peticiones correctas que devolverán el resultado como incorrectas que provocarán un error.

Los mensajes se envían codificados en JSON y usan el fin de línea ```/n``` para indicar la terminación.

Para identificar el flujo de datos entre clientes y servidor en el lado del cliente, se ha identificado cada petición en consola mediante los
términos "PREG" y "RESP" junto al número de cliente al cual referencian.

## Server.py
El servidor se ejecuta mediante un *ThreadingTCPServer* el cual permite atender a múltiples peticiones sin provocar bloqueos ni esperas.

El servidor se encarga de conducir todo el ciclo pertinente: identificación del cliente, decodificación de su solicitud,
verificación de la validez de la misma y transmisión de la respuesta correspondiente a esta. Este implementa las operaciones de
suma, resta, multiplicación, división, raíz cuadrada, media y desviación poblacional junto a las limitaciones de argumentos de cada una.

Las limitaciones de las operaciones vienen o bien ligadas a la naturaleza de la operación o bien establecidas por el programador.
Por defecto, las operaciones de suma, resta, media y desviación poblacional se han definido como operaciones compuestas por lo que permiten operar sobre una lista de números (≥2), mientras que las operaciones de multiplicación y división se han definido como operaciones atómicas (aunque pueden hacerse compuestas simplemente modificando el límite de argumentos).

El identificador de cada petición viene dada por la conjunción de:
- La IP y el número de puerto asignado al cliente.
- Un identificador interno del servidor que etiqueta numéricamente a cada proceso nuevo que llega

### LOG
El servidor registra en un historial de los diferentes sucesos ocurridos durante todo el ciclo, cada registro viene con el identificador
de petición al inicio y precedido por una etiqueta con el tipo de registro. Los tipos presentes son los siguientes:

**[INFO]**:
  - **SERVSTART**: Inicialización del servidor.
  - **SERVSTOP**: Cierre del servidor.
  - **CONNSTART**: Conexión de un nuevo cliente, con su identificador propio y el número de clientes activos en ese momento.
  - **CONNEND**: Finalización de un cliente, muestra las conexiones activas restantes, las peticiones atendidas hasta el momento, el número de errores total y la cantidad de datos enviados/recibidos.
  - **REQNEW**: Nueva solicitud, muestra el contenido decodificado de la petición.
  - **REQEND**: Fin del procesado de la solicitud, muestra un flag de ok (no error), tiempo de respuesta y datos enviados/recibidos.
<br>

**[ERROR]**:
- **REQERR**: Error de solicitud, cuando la instrucción no esta correctamente formulada o se está intentando realizar una operación no permitida.
<br>
<br>

Observaciones:
1. Pese a que los cálculos incluyen los números "completos", por razones estéticas se ha limitado de 15 A 3 el número de dígitos decimales en la impresión por consola (redondeo)
2. Se ha sopesado la opción de incluir un acumulador, sin embargo en nuestro experimento un cliente genera múltiples peticiones independientes e interpreta su resultado por lo que no vemos la diferencia que un acumulador supondría sobre las condiciones del experimento.
