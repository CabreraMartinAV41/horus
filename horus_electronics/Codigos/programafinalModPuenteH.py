from machine import Pin, PWM
from time import sleep

# Configuración de los pines GPIO para los motores DC con Puente H
velmot1pwm = PWM(Pin(10))
velmot2pwm = PWM(Pin(13))
mot1a = Pin(11, Pin.OUT)  # Dirección del motor 1
mot1b = Pin(12, Pin.OUT)
mot2a = Pin(14, Pin.OUT)  # Dirección del motor 2
mot2b = Pin(15, Pin.OUT)

# Configurar la frecuencia de PWM (suele ser 1kHz para motores DC)
velmot1pwm.freq(1000)
velmot2pwm.freq(1000)

# Pines de control del brazo tijera y el servo
dirB = Pin(8, Pin.OUT)   # Dirección del motor del brazo
stepB = Pin(7, Pin.OUT)  # Paso del motor del brazo
servo_pin = Pin(2)       # Pin para el control del servo (PWM)

# Configuración del PWM para el servomotor
servo_pwm = PWM(servo_pin)
servo_pwm.freq(50)  # Frecuencia de 50Hz (20 ms de período)

# Pines para los pulsos de inicio y cámara
pulso_in_rpi4 = Pin(1, Pin.IN)
pulso_out_rpi4 = Pin(0, Pin.OUT)



def mover_motores(sentido, velocidad, duracion):
    """
    Función para controlar dos motores DC con un puente H y PWM.
    Los motores se moverán en el mismo sentido y al mismo tiempo.
    
    Argumentos:
        sentido (str): 'fw' para avanzar o 'bw' para retroceder.
        velocidad (int): Velocidad de PWM (0 a 100).
        duracion (float): Tiempo en segundos que los motores deben moverse.
    """
    velocidad2 = (velocidad*65535)/100 
    print(int(velocidad2))
    if sentido == "fw":
        mot1a.on()
        mot1b.off()
        mot2a.on()
        mot2b.off()
    elif sentido == "bw":
        mot1a.off()
        mot1b.on()
        mot2a.off()
        mot2b.on()
    else:
        print("Sentido no válido")
        return

    # Establecer la velocidad de PWM
    velmot1pwm.duty_u16(int(velocidad2))
    velmot2pwm.duty_u16(int(velocidad2))

    # Mantén los motores en movimiento durante el tiempo especificado
    sleep(duracion)

    # Detiene los motores
    mot1a.off()
    mot1b.off()
    mot2a.off()
    mot2b.off()
    velmot1pwm.duty_u16(0)
    velmot2pwm.duty_u16(0)


def mover_stepper(dir_pin, step_pin, pasos, direccion, delay):
    dir_pin.value(direccion)
    for _ in range(pasos):
        step_pin.on()
        sleep(delay)
        step_pin.off()
        sleep(delay)

# Función principal para ejecutar la secuencia
def detectar_pulso():
    esperar_pulso("Iniciar secuencia")
    pulsostartrecibido()

def pulsostartrecibido():
    print("Arrancando motores de orugas...")
    mover_motores("fw", 50, 2)  # Mueve los motores adelante a 50% de velocidad por 2 segundos
    print("Motores funcionando durante 1 segundo...")
    sleep(1)
    brazoup()

def brazoup():
    print("Levantando brazo hasta el tope...")
    mover_stepper(dirB, stepB, pasos=600, direccion=1, delay=0.01)
    esperapulsocamara()

def esperapulsocamara():
    esperar_pulso("Esperando pulso de la cámara")
    pulsocamararecibido()

def pulsocamararecibido():
    print("Iniciando paneo del servo...")
    mover_servo_paneo()
    terminaservo()

# Control del servo para paneo de 0 a 180 grados en intervalos de 30 grados y luego regresar
def mover_servo_paneo():
    print("Moviendo el servo de 0 a 180 grados en intervalos de 30 grados...")
    for angulo in range(0, 181, 30):
        mover_servo(angulo)
        sleep(0.5)
    
    print("Moviendo el servo de 180 a 0 grados en intervalos de 30 grados...")
    for angulo in range(180, -1, -30):
        mover_servo(angulo)
        sleep(0.5)

# Función para mover el servo a una posición específica usando PWM real
def mover_servo(angulo):
    # Convertir el ángulo a ciclo de trabajo PWM
    duty_cycle = angle_to_duty_cycle(angulo)
    servo_pwm.duty_u16(duty_cycle)  # Ajustar ciclo de trabajo
    print(f"Servo movido a {angulo} grados con ciclo de trabajo {duty_cycle}")

# Función para convertir un ángulo (0-180) a ciclo de trabajo PWM
def angle_to_duty_cycle(angulo):
    # El ciclo de trabajo para el servo varía de 1ms (0 grados) a 2ms (180 grados).
    # En términos de ciclo de trabajo para una señal de 50 Hz:
    # - 1 ms corresponde aproximadamente a un ciclo de trabajo de 5% (3276 en valor de 16 bits)
    # - 2 ms corresponde aproximadamente a un ciclo de trabajo de 10% (6553 en valor de 16 bits)
    # Mapear el rango 0-180 grados al rango 3276-6553
    min_duty = 3276   # 5% de ciclo de trabajo (1 ms)
    max_duty = 6553   # 10% de ciclo de trabajo (2 ms)
    return int(min_duty + (angulo / 180.0) * (max_duty - min_duty))

def terminaservo():
    print("Enviando pulso a la Raspberry Pi 4...")
    sleep(3)
    print("Esperando 3 segundos...")
    brazodown()

def brazodown():
    print("Bajando brazo hasta el tope...")
    mover_stepper(dirB, stepB, pasos=600, direccion=0, delay=0.002)
    movermotoresfinal()

def movermotoresfinal():
    print("Moviendo los motores de orugas nuevamente...")
    mover_motores("fw", 50, 2)  # Mueve los motores adelante a 50% de velocidad por 2 segundos
    print("Movimiento finalizado. Programa concluido.")

def esperar_pulso(mensaje):
    while True:
        pulso = input(f"{mensaje} (Escribe '1' para enviar pulso): ")
        if pulso == '1':
            print("Pulso detectado.")
            return
        else:
            print("Pulso no detectado, esperando...")

# Iniciar la simulación
detectar_pulso()