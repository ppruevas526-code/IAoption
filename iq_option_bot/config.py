"""
Configuración central del bot.
Las credenciales se leen desde variables de entorno (archivo .env)
"""
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# =============================================
# CREDENCIALES
# =============================================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

# =============================================
# SELECCIÓN DE ACTIVO (NUEVA FUNCIÓN)
# =============================================
# Lista de activos disponibles para elegir
ACTIVOS_DISPONIBLES = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "EURJPY"]

def elegir_activo():
    """Pregunta al usuario qué activo quiere analizar al iniciar el bot."""
    print("\n" + "="*40)
    print("🎯 SELECCIÓN DE ACTIVO")
    print("="*40)
    for i, activo in enumerate(ACTIVOS_DISPONIBLES, 1):
        print(f"  {i}. {activo}")
    
    while True:
        try:
            opcion = input("\n👉 Elige el número del activo a analizar: ").strip()
            indice = int(opcion) - 1
            if 0 <= indice < len(ACTIVOS_DISPONIBLES):
                activo_elegido = ACTIVOS_DISPONIBLES[indice]
                print(f"✅ Activo seleccionado: {activo_elegido}\n")
                return [activo_elegido]  # Retorna una lista con el activo elegido
            else:
                print("❌ Número fuera de rango. Intenta de nuevo.")
        except ValueError:
            print("❌ Por favor, ingresa solo un número.")

# =============================================
# PARÁMETROS DE TRADING
# =============================================
# Si el bot se ejecuta directamente, pregunta el activo.
# Si se importa desde main.py, también puedes llamar a elegir_activo() allí.
ACTIVOS = ["EURUSD"]   # Se sobrescribe tras el análisis inicial en main.py

TIEMPO_VELA = 300        # 5 minutos
CANTIDAD_VELAS = 150     # Más velas para mejor análisis IA
MONTO = 1.0
DURACION = 5              # minutos de duración de la operación
MODO_REAL = False
MAX_OPERACIONES_POR_DIA = 30
MAX_PERDIDA_DIARIA = 10.0
MIN_CONFIANZA_IA = 0.65   # Umbral mínimo de confianza para operar

# =============================================
# OTROS
# =============================================
ARCHIVO_MEMORIA_IA = os.path.join("data", "ia_memoria.json")
CACHE_DISPONIBILIDAD_SEGUNDOS = 300