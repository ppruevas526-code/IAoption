"""
Configuración central del bot.
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
# LISTA DE ACTIVOS
# =============================================
ACTIVOS_DISPONIBLES = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
    "EURJPY", "EURGBP", "EURAUD", "EURCAD", "EURCHF",
    "GBPJPY", "GBPAUD", "GBPCAD", "GBPCHF",
    "AUDJPY", "AUDCAD", "AUDCHF", "AUDNZD",
    "CADJPY", "CADCHF", "CHFJPY",
    "NZDJPY", "NZDCAD", "NZDCHF",
    "BTCUSD", "ETHUSD", "LTCUSD", "XRPUSD", "BCHUSD",
    "XAUUSD", "XAGUSD",
    "US30", "UK100",
]

def elegir_activo():
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
                return [ACTIVOS_DISPONIBLES[indice]]
            print("❌ Número fuera de rango.")
        except ValueError:
            print("❌ Ingresa solo un número.")

# =============================================
# PARÁMETROS DE TRADING
# =============================================
ACTIVOS = ["EURUSD"]
TIEMPO_VELA = 300
CANTIDAD_VELAS = 150
MONTO = 1.0
DURACION = 5
MODO_REAL = False
MAX_OPERACIONES_POR_DIA = 30
MAX_PERDIDA_DIARIA = 10.0
MIN_CONFIANZA_IA = 0.0

# =============================================
# OTROS
# =============================================
ARCHIVO_MEMORIA_IA = os.path.join("data", "ia_memoria.json")
CACHE_DISPONIBILIDAD_SEGUNDOS = 300

# =============================================
# MODO APRENDIZAJE
# =============================================
MODO_APRENDIZAJE = True

# =============================================
# IGNORAR VERIFICACIÓN DE DISPONIBILIDAD
# =============================================
# True = intenta operar aunque la API no reporte el activo como operable.
# La API de IQ Option tiene problemas conocidos al reportar activos,
# por lo que esta opción evita bloqueos falsos.
IGNORAR_DISPONIBILIDAD = True