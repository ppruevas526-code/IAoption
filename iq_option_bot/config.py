"""
Configuración central del bot - VERSIÓN FLEXIBLE
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
EMAIL = os.getenv("IQ_EMAIL") or "ppruevas526@gmail.com"
PASSWORD = os.getenv("IQ_PASSWORD") or "Crepes.2026*"

# =============================================
# LISTA DE ACTIVOS (FOREX + OTC + CRIPTO + MATERIAS PRIMAS)
# =============================================
ACTIVOS_DISPONIBLES = [
    # ===== FOREX MAYORES =====
    "EURUSD", "EURUSD-OTC",
    "GBPUSD", "GBPUSD-OTC",
    "USDJPY", "USDJPY-OTC",
    "AUDUSD", "AUDUSD-OTC",
    "USDCAD", "USDCAD-OTC",
    "USDCHF", "USDCHF-OTC",
    "NZDUSD", "NZDUSD-OTC",

    # ===== FOREX CRUZADOS =====
    "EURJPY", "EURJPY-OTC",
    "EURGBP", "EURGBP-OTC",
    "EURAUD", "EURAUD-OTC",
    "EURCAD", "EURCAD-OTC",
    "GBPJPY", "GBPJPY-OTC",
    "GBPAUD", "GBPAUD-OTC",
    "AUDJPY", "AUDJPY-OTC",
    "CADJPY", "CADJPY-OTC",
    "CHFJPY", "CHFJPY-OTC",

    # ===== CRIPTOMONEDAS =====
    "BTCUSD", "BTCUSD-OTC",
    "ETHUSD", "ETHUSD-OTC",
    "LTCUSD", "LTCUSD-OTC",

    # ===== MATERIAS PRIMAS =====
    "XAUUSD", "XAUUSD-OTC",
    "XAGUSD", "XAGUSD-OTC",

    # ===== ÍNDICES =====
    "US30-OTC",
    "US100-OTC",
    "GER30-OTC",
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
# 🔥 PARÁMETROS DE TRADING - FLEXIBLES
# =============================================
# Si dejas ACTIVOS = [] el bot analizará TODOS los de la lista
ACTIVOS = []                 # Vacío = analiza todos

TIEMPO_VELA = 60             # ⏱️ 1 minuto → muchas más señales
CANTIDAD_VELAS = 100         # Velas históricas

MONTO = 1.0                  # 💰 Monto por operación
DURACION = 1                 # ⏳ Duración en minutos

MODO_REAL = False            # 🔒 DEMO primero
MAX_OPERACIONES_POR_DIA = 30
MAX_PERDIDA_DIARIA = 20.0

# =============================================
# 🔥 FILTROS DE IA - MUY FLEXIBLES
# =============================================
MIN_CONFIANZA_IA = 0.15      # 🎯 Bajo para que la IA decida casi todo
CONFIANZA_IA_PARA_DECIDIR = 0.25  # Confianza mínima para que la IA elija dirección

# =============================================
# OTROS
# =============================================
ARCHIVO_MEMORIA_IA = os.path.join("data", "ia_memoria.json")
CACHE_DISPONIBILIDAD_SEGUNDOS = 120

# =============================================
# 🔥 MODOS ESPECIALES - ACTIVADOS
# =============================================
MODO_APRENDIZAJE = True      # Fuerza operaciones (usa IA o aleatorio)
IGNORAR_DISPONIBILIDAD = True  # Ignora bloqueos de la API
FORZAR_OPERACION = True      # Convierte ESPERAR en CALL/PUT