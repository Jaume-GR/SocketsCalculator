"""
Servidor TCP

Recibe peticiones JSON y devuelve resultados o errores.
Registra conexiones, peticiones, bytes y tiempos de respuesta.
"""

import logging as log
import socketserver
import statistics
import threading
import math
import json
import time

from datetime import datetime

metlock = threading.Lock()
metrics = {
    "active_connections" : 0,
    "attended_requests" : 0,
    "errors" : 0,
    "bytes_rx" : 0,
    "bytes_tx" : 0
}

log.basicConfig(
    filename="servidor.log",
    level=log.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%d/%m %H:%M:%S",
    encoding="utf-8"
)

MAX_ARG_NUM = 10 # límite ficticio (funciona con más argumentos)
instructions = { # op : [argmin, argmax]
    "add" : [2, MAX_ARG_NUM],
    "sub" : [2, MAX_ARG_NUM],
    "mult": [2, 2],
    "div" : [2, 2],
    "sqrt": [1, 1],
    "mean": [2, MAX_ARG_NUM],
    "std" : [2, MAX_ARG_NUM]
 }
operations = list(instructions.keys())

class DateHandler(socketserver.StreamRequestHandler):
    def handle(self):
        ip, port = self.client_address
        client_id = f"{ip}:{port}"
        req_count = 0 # Cuenta el número de peticiones de un mismo puerto, se usa para el ID
        with metlock: metrics["active_connections"] += 1
        log.info(" CONNSTART ID:%s [activas=%d]", client_id, metrics["active_connections"])

        try:
            while True:
                data = self.rfile.readline()
                print("Datos recibidos:", repr(data))
                if not data: return

                with metlock:
                    metrics["bytes_rx"] += len(data)
                    metrics["attended_requests"] += 1
                req_count += 1
                request_id = f"{client_id}-{req_count}" 

                start = time.perf_counter()

                peticion = json.loads(data.decode("utf-8"))
                log.info(" REQNEW    ID:%s content: '%s %s'", request_id, peticion["op"], " ".join(f"{x:.3f}" for x in peticion["args"]))
                
                ok, arg = command_processor(peticion)
                if not ok:
                    with metlock: metrics["errors"] += 1
                    log.error("REQERR    ID:%s arg: %s", request_id, arg)
                respuesta = {"ok": ok, "result" if ok else "error" : arg if ok else f"Error: {arg}"}

                encodedResponse = (json.dumps(respuesta) + "\n").encode("utf-8")
                self.request.sendall(encodedResponse)
                with metlock: metrics["bytes_tx"] += len(encodedResponse)

                elapsed_ms = (time.perf_counter() - start) * 1000
                log.info(" REQEND    ID:%s ok=%s time_ms=%.3f bytes_rx=%d bytes_tx=%d",
                        request_id,
                        respuesta["ok"],
                        elapsed_ms,
                        len(data),
                        len(encodedResponse))
        finally:
            with metlock: metrics["active_connections"] -= 1
            log.info(f" CONNEND   ID:{client_id} %s", ", ".join(f"{clau}: {valor}" for clau, valor in metrics.items()))



def command_processor(data):
    op = data["op"]
    if op not in operations:
        return (False, f"la operación '{op}' no existe o no se encuentra implementada")
    numeros = data["args"]
    if not(numeros and isinstance(numeros, list) and all(type(x) in (int, float) for x in numeros)):
        return (False, f"la lista {numeros} no es válida")
    argmin = instructions[op][0]
    argmax = instructions[op][1]
    if len(numeros) < argmin : return (False, f"la instrucción requiere de como mínimo 2 argumentos (números), [{op} arg1 arg2]")
    if len(numeros) > argmax : return (False, f"demasiados argumentos! [{op} arg1{f" ... arg{argmax}" if argmax > 1 else ""}]")
    
    if op == "add" : return (True, sum(data["args"]))
    if op == "sub" : return (True, numeros[0] - sum(numeros[1:]))
    if op == "mult": return (True, numeros[0] * numeros[1])
    if op == "div" :
        if numeros[1] == 0: return (False, "se está intentando dividir por 0 (infinito)")
        else : return (True, numeros[0] / numeros[1])
    if op == "sqrt" :
        if numeros[0] < 0: return (False, "la raíz cuadrada se debe hacer sobre un número positivo")
        else : return (True, math.sqrt(numeros[0]))
    if op == "mean" : return (True, sum(numeros) / len(numeros))
    if op == "std"  : return (True, statistics.pstdev(numeros)) # Desviación poblacional
    

with socketserver.ThreadingTCPServer(('', 5088), DateHandler) as server: # localhost:5088
    print("El servidor calculadora está funcionando...")
    try:
        log.info(" SERVSTART Server started.")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor calculadora detenido.\n")
        log.info(" SERVSTOP  Server stopped.")