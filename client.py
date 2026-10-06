"""
Experimento Clientes TCP

Lanza múltiples clientes TCP.
Genera y envía peticiones JSON al servidor e
imprime el resultado de cada una
"""
import threading
import socket
import random
import json
import time

host = "localhost"
port = 5088
operations = ["add", "sub", "div", "mult", "sqrt", "mean", "std"]

# Parámetros principales
client_qty = 2      # Número de clientes
rate = 2.0          # Peticiones/segundo
exp_duration = 10   # Duración del experimento

# Otros 
lbound = 0          # Límite inferior del PRNG
ubound = 100        # Límite superior del PRNG
max_argn = 5        # Cantidad máxima de números por operación que generará el PRNG
dsize = 2           # Número de decimales mostrados por consola

def run_client(client_id, rate, exp_duration):
    # Creamos un socket TCP (SOCK_STREAM)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))

        # Calculamos el tiempo de finalización y creamos el canal de comunicación
        start_time = time.perf_counter()
        final = start_time + exp_duration
        next_time = start_time
        channel = sock.makefile("rb")

        try: 
            while True:
                # Calculamos el tiempo de espera hasta la siguiente petición
                # siguiendo una tasa dada y una distribución exponencial
                next_time += random.expovariate(rate)
                if next_time >= final : break
                time.sleep(max(0, next_time - time.perf_counter()))
                if time.perf_counter() >= final : break
                
                # Tomamos una operación al azar de las implementadas
                operation = random.choice(operations)
                # Permitimos la generación de algunas instrucciones incorrectas
                argn = random.randint(1, max_argn if operation not in ["div", "mult", "sqrt"] else 2)
                # Hacemos que algunas instrucciones se generen con números enteros y otros con decimales
                randgen = random.choice([random.randint, random.uniform])
                numbers = [randgen(lbound, ubound) for _ in range(argn)]
                instruction = {"op": operation, "args" : numbers}
                print(f"[PREG Cliente {client_id}]:- {operation} {' '.join(str(x) if isinstance(x, int) else f'{x:.{dsize}f}' for x in numbers)}")
                # Mandamos la petición al servidor en formato JSON
                sock.sendall((json.dumps(instruction) + "\n").encode("utf-8"))

                received = channel.readline() # Recibe los datos del servidor
                if not received:
                    print("El servidor ha cerrado la conexión.")
                    break
                response = json.loads(received.decode("utf-8"))
                print(f"[RESP Cliente {client_id}]:- " + (
                      f"El resultado es {str(response["result"]) if isinstance(response["result"], int) else f'{response["result"]:.{dsize}f}'}."
                      if response["ok"] else response["error"]) + "\n")
        finally:
            channel.close()


def main():
    threads = []

    for client_id in range(1, client_qty + 1):
        thread = threading.Thread(target=run_client, args=(client_id, rate, exp_duration))
        threads.append(thread)
        thread.start()

    for thread in threads: 
        thread.join()

    print("\nEl test ha finalizado.\n")

if __name__ == "__main__": main()