__author__ = 'agustinsalas'

import datetime
import MySQLdb as motor
import numpy as np
import random
import math
from scipy.stats import bernoulli

from Parseo_Archivo import parsear
from Parseo_Archivo import getCantidadColumnas
from Parseo_Archivo import getCantidadFilas
from Parseo_Archivo import getVectorCosto
from Parseo_Archivo import getMatrizA


# PARAMETROS PARA TRABAJAR LA MH
HARMONY_MEMORY_SIZE = 5
MAX_IMPROVISACIONES = 1000
HMCR_MAX = 0.95  # 0.95 sugerido
HMCR_MIN = 0.05  # 0.3 sugerido
PAR = 0.005  # 0.75 sugerido
IMPROVISACION = 1
BERNOULLI_P = 0.5  # http://es.wikipedia.org/wiki/Ensayo_de_Bernoulli
MUTATION_P = 0.5  # http://en.wikipedia.org/wiki/Mutation_(genetic_algorithm)
SEED = 0
RANDOM_UNO = 0
INDEX_BEST_HARMONY = 0
INDEX_WORST_HARMONY = 0

# VARIABLES GLOBALES
HARMONY_MEMORY = []
BEST_HARMONY = []
WORST_HARMONY = []

EXECUTION_REGISTER_ID = 0

# IMPLEMENTADA
def iniciacionHM():
    global HARMONY_MEMORY
    insertExe_REGISTER()
    genera_poblacion_inicial(HARMONY_MEMORY)
    nueva_armonia = nueva_armonia_agresiva()
    HARMONY_MEMORY.append(nueva_armonia)
    almacenaMejorYPeorArmonia()

# IMPLEMENTADA
def nueva_armonia_agresiva():
    """
    Mientras mas alto es el costo, menor es la ganancia
    :return:
    """
    mu_j = []
    vector_costo = getVectorCosto()
    for costo in vector_costo:
        mu_j.append(1 / float(costo))
    matriz_a = getMatrizA()
    nueva_armonia = np.zeros(getCantidadColumnas(), dtype=np.int)
    for row in matriz_a:
        costo_fila = row * mu_j
        menor_costo = max(mu_j)
        posicion_menor_costo = 0
        posicion_columna = 0
        for variable in costo_fila:
            if 0 < variable < menor_costo:
                menor_costo = variable
                posicion_menor_costo = posicion_columna
            posicion_columna += 1
        if posicion_menor_costo < getCantidadColumnas() - 1:
            nueva_armonia[posicion_menor_costo] = 1
    # print nueva_armonia
    fitness = evaluarConFuncionObjetivo(nueva_armonia)

    # print "Valor armonia agresiva: " + str(fitness)

    return nueva_armonia

# IMPLEMENTADA
def genera_poblacion_inicial(HARMONY_MEMORY):
    i = 0
    while i < HARMONY_MEMORY_SIZE:
        vectorGenerado = bernoulli.rvs(BERNOULLI_P, size=getCantidadColumnas())
        HARMONY_MEMORY.append(vectorGenerado)
        # print vectorGenerado
        i += 1

# IMPLEMENTADA
def reparacion_de_armonia(vector_armonia):
    print "Valor armonia original: " + str(evaluarConFuncionObjetivo(vector_armonia))
    a_transpuesta = np.transpose(getMatrizA())
    matriz_a = getMatrizA()
    armonia_temporal = []
    restriccion_incumplida = []
    restriccion_incumplida = np.dot(vector_armonia, a_transpuesta)

    # Fase ADD
    i = 0
    for restriccion in restriccion_incumplida:
        if restriccion == 0:
            row = matriz_a[i]
            j = 0
            for tono in row:
                if tono == 1:
                    break
                j += 1
            vector_armonia[j] = 1

        i += 1

    armonia_temporal = vector_armonia

    # Fase DROP

    for restriccion in matriz_a:

        target = 1
        for index, val in enumerate(restriccion):
            if val == 1:
                lastIndexOf = index

        armonia_temporal[lastIndexOf] = 0
        if not cumple_restricciones(armonia_temporal):
            armonia_temporal[lastIndexOf] = 1

    vector_armonia = armonia_temporal
    print "Valor armonia reparada: " + str(evaluarConFuncionObjetivo(vector_armonia))

    return vector_armonia

# IMPLEMENTADA
def cumple_restricciones(vector_armonia):
    a_transpuesta = np.transpose(getMatrizA())
    restriccion_incumplida = np.dot(vector_armonia, a_transpuesta)
    cumple = True

    for restriccion in restriccion_incumplida:
        if restriccion == 0:
            cumple = False

    if cumple:
        return True
    else:
        return False

# IMPLEMENTADA
def evaluarConFuncionObjetivo(armonia):
    vector_costo = getVectorCosto()
    armonia = armonia * vector_costo
    sumatoria = 0
    for tono in armonia:
        sumatoria = sumatoria + tono

    return sumatoria

# IMPLEMENTADA
def almacenaMejorYPeorArmonia():
    global INDEX_BEST_HARMONY
    global INDEX_WORST_HARMONY
    global BEST_HARMONY
    global WORST_HARMONY

    costo_armonia = []
    for armonia in HARMONY_MEMORY:
        valor_evaluado = evaluarConFuncionObjetivo(armonia)
        costo_armonia.append(valor_evaluado)
    INDEX_BEST_HARMONY = sorted(range(len(costo_armonia)), key=lambda x: costo_armonia[x])[0]
    INDEX_WORST_HARMONY = sorted(range(len(costo_armonia)), key=lambda x: costo_armonia[x], reverse=True)[0]

    BEST_HARMONY = HARMONY_MEMORY[INDEX_BEST_HARMONY]
    WORST_HARMONY = HARMONY_MEMORY[INDEX_WORST_HARMONY]

    insert_best_and_worst()

# IMPLEMENTADA
def calcularHMCR(FEs):
    # Implementar calculo de Harmony Memory Consideration Rate
    global HMCR_MAX
    global HMCR_MIN
    global MAX_IMPROVISACIONES

    hmcr_t = HMCR_MAX - ((HMCR_MAX - HMCR_MIN) / float(MAX_IMPROVISACIONES)) * FEs
    return hmcr_t

# IMPLEMENTADA
def crearNuevaArmonia(iteador_t):
    """

    :rtype : Retorna un vector con la nueva armonia improvisada
    """
    nueva_armonia = np.zeros(getCantidadColumnas(), dtype=np.int)
    insert_best_and_worst()
    """ El vector tupla_mejor_armonia guarda en su primera posicion, el indice de la solucion mas barata,
        El segundo elemento guarda el valor de la solucion mas barata"""

    mejor_armonia = HARMONY_MEMORY[INDEX_BEST_HARMONY]
    j = 0
    while j < getCantidadColumnas() - 1:
        # random.seed(SEED)
        numero_random = random.random()
        numero_random2 = random.random()
        hmcr_calculado = calcularHMCR(iteador_t)
        if numero_random <= hmcr_calculado:
            # print "Se realiza ajuste de HMCR tono mejor armonia a actual"
            nueva_armonia[j] = mejor_armonia[j]
        else:
            a = random.randint(0, HARMONY_MEMORY_SIZE - 1)
            while a == INDEX_BEST_HARMONY:
                a = random.randint(0, HARMONY_MEMORY_SIZE - 1)
            vector_a = HARMONY_MEMORY[a]
            nueva_armonia[j] = vector_a[j]
            if numero_random2 <= PAR:
                # print "Se realiza mutacion genetica"
                nueva_armonia[j] = math.fabs(nueva_armonia[j] - 1)
        j += 1

    #print "costo nueva armonia: " + str(evaluarConFuncionObjetivo(nueva_armonia))

    return nueva_armonia

# IMPLEMENTADA
def mejorIgualQueBest(nuevaArmonia):
    if evaluarConFuncionObjetivo(nuevaArmonia) <= evaluarConFuncionObjetivo(HARMONY_MEMORY[INDEX_BEST_HARMONY]):
        return True
    else:
        return False

# IMPLEMENTADA
def mejorIgualQueWorst(nuevaArmonia):
    if evaluarConFuncionObjetivo(nuevaArmonia) <= evaluarConFuncionObjetivo(HARMONY_MEMORY[INDEX_WORST_HARMONY]):
        return True
    else:
        return False

# IMPLEMENTADA
def reemplazarMejor(nuevaArmonia):
    global INDEX_BEST_HARMONY
    HARMONY_MEMORY.append(nuevaArmonia)
    INDEX_BEST_HARMONY = len(HARMONY_MEMORY) - 1

# IMPLEMENTADA
def reemplazarPeor(nuevaArmonia):
    global INDEX_WORST_HARMONY
    global HARMONY_MEMORY
    HARMONY_MEMORY[INDEX_WORST_HARMONY] = nuevaArmonia

# IMPLEMENTADA
def insert_best_and_worst():
    global EXECUTION_REGISTER_ID
    global HARMONY_MEMORY
    global INDEX_BEST_HARMONY
    global INDEX_WORST_HARMONY

    print "Mejor Valor: " + str(evaluarConFuncionObjetivo(HARMONY_MEMORY[INDEX_BEST_HARMONY]))
    print "Peor Valor: " + str(evaluarConFuncionObjetivo(HARMONY_MEMORY[INDEX_WORST_HARMONY]))

    try:
        conn = motor.connect(host="sagalid.cl", user="harmony", passwd="harmony2015", db="harmony")
        cur = conn.cursor()
        cur.execute("INSERT INTO BEST_AND_WORST VALUES ("
                    "NULL, "
                    "%s, "
                    "%s, "
                    "%s, "
                    "%s, "
                    "%s)",
                    (EXECUTION_REGISTER_ID,
                     evaluarConFuncionObjetivo(HARMONY_MEMORY[INDEX_BEST_HARMONY]),
                     evaluarConFuncionObjetivo(HARMONY_MEMORY[INDEX_WORST_HARMONY]),
                     INDEX_BEST_HARMONY,
                     INDEX_WORST_HARMONY))
        conn.commit()
    except motor.Error as errorValue:
        print("Error al insertar Mejor y Peor armonia: {}".format(errorValue))
    finally:
        cur.close()
        del cur
        conn.close()

# IMPLEMENTADA
def insertExe_REGISTER():
    global EXECUTION_REGISTER_ID
    try:
        conn = motor.connect(host="sagalid.cl", user="harmony", passwd="harmony2015", db="harmony")
        cur = conn.cursor()
        now = datetime.datetime.now()
        a = now.strftime('%Y-%m-%d %H:%M:%S')
        cur.execute("INSERT INTO EXE_REGISTER VALUES ("
                    "NULL, "
                    "%s, "
                    "%s, "
                    "%s, "
                    "%s, "
                    "%s, "
                    "%s, "
                    "%s, "
                    "%s, "
                    "%s, "
                    "%s, "
                    "%s, "
                    "%s)",
                    (HARMONY_MEMORY_SIZE,
                     MAX_IMPROVISACIONES,
                     HMCR_MAX,
                     HMCR_MIN,
                     PAR,
                     BERNOULLI_P,
                     MUTATION_P,
                     INDEX_BEST_HARMONY,
                     INDEX_WORST_HARMONY,
                     SEED,
                     a,
                     a))
        conn.commit()
        EXECUTION_REGISTER_ID = cur.lastrowid
        print "ID Registro " + str(EXECUTION_REGISTER_ID)
    except motor.Error as errorValue:
        print("Error al insertar registro de ejecucion: {}".format(errorValue))
    finally:
        cur.close()
        del cur
        conn.close()

# IMPLEMENTADA
def ejecucionMH():
    global HARMONY_MEMORY
    parsear(['scp41.txt'])  # Permite parsear varios archivos, pasandolos como listas.
    iniciacionHM()

    i = 0
    for armonia_en_hm in HARMONY_MEMORY:
        armonia_reparada = reparacion_de_armonia(armonia_en_hm)
        HARMONY_MEMORY[i] = armonia_reparada
        i += 1

    i = 1
    while i < MAX_IMPROVISACIONES:
        print "<--------------------INI de la ejecucion: ", (i), "-------------------->"
        almacenaMejorYPeorArmonia()
        nuevo_vector_armonia = crearNuevaArmonia(i)
        nuevo_vector_armonia = reparacion_de_armonia(nuevo_vector_armonia)

        if mejorIgualQueBest(nuevo_vector_armonia):
            reemplazarMejor(nuevo_vector_armonia)
        elif mejorIgualQueWorst(nuevo_vector_armonia):
            reemplazarPeor(nuevo_vector_armonia)

        insert_best_and_worst()
        # Incrementa la Improvisacion en uno
        # print "Elementos en HM: " + str(len(HARMONY_MEMORY))
        print "<--------------------FIN de la ejecucion: ", (i), "-------------------->"
        i += 1

# IMPLEMENTADA
def main():
    ejecucionMH()


main()
