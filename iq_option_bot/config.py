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
# LISTA AMPLIADA DE ACTIVOS BINARIOS
# =============================================
# Puedes comentar (con #) los que no te interesen.
# Si un activo da error "pocas velas", es que IQ Option no lo reconoce
# con ese nombre exacto en tu cuenta/región.
ACTIVOS_DISPONIBLES = [
    # ===== FOREX MAYORES =====
    "EURUSD",   # Euro / Dólar
    "GBPUSD",   # Libra / Dólar
    "USDJPY",   # Dólar / Yen
    "AUDUSD",   # Dólar Australiano / Dólar
    "USDCAD",   # Dólar / Dólar Canadiense
    "USDCHF",   # Dólar / Franco Suizo
    "NZDUSD",   # Dólar Neozelandés / Dólar

    # ===== FOREX CRUZADOS =====
    "EURJPY",   # Euro / Yen
    "EURGBP",   # Euro / Libra
    "EURAUD",   # Euro / Dólar Australiano
    "EURCAD",   # Euro / Dólar Canadiense
    "EURCHF",   # Euro / Franco Suizo
    "GBPJPY",   # Libra / Yen
    "GBPAUD",   # Libra / Dólar Australiano
    "GBPCAD",   # Libra / Dólar Canadiense
    "GBPCHF",   # Libra / Franco Suizo
    "AUDJPY",   # Dólar Australiano / Yen
    "AUDCAD",   # Dólar Australiano / Dólar Canadiense
    "AUDCHF",   # Dólar Australiano / Franco Suizo
    "AUDNZD",   # Dólar Australiano / Dólar Neozelandés
    "CADJPY",   # Dólar Canadiense / Yen
    "CADCHF",   # Dólar Canadiense / Franco Suizo
    "CHFJPY",   # Franco Suizo / Yen
    "NZDJPY",   # Dólar Neozelandés / Yen
    "NZDCAD",   # Dólar Neozelandés / Dólar Canadiense
    "NZDCHF",   # Dólar Neozelandés / Franco Suizo

    # ===== CRIPTOMONEDAS =====
    "BTCUSD",   # Bitcoin
    "ETHUSD",   # Ethereum
    "LTCUSD",   # Litecoin
    "XRPUSD",   # Ripple
    "BCHUSD",   # Bitcoin Cash

    # ===== MATERIAS PRIMAS =====
    "XAUUSD",   # Oro
    "XAGUSD",   # Plata
    "WTIUSD",   # Petróleo WTI
    "BRTUSD",   # Petróleo Brent

    # ===== ÍNDICES =====
    "US100",    # NASDAQ 100
    "US500",    # S&P 500
    "US30",     # Dow Jones
    "GER30",    # DAX Alemán
    "UK100",    # FTSE 100
    "JP225",    # Nikkei 225
]

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
                return [activo_elegido]
            else:
                print("❌ Número fuera de rango. Intenta de nuevo.")
        except ValueError:
            print("❌ Por favor, ingresa solo un número.")

# =============================================
# PARÁMETROS DE TRADING
# =============================================
ACTIVOS = ["EURUSD"]   # Se sobrescribe tras el análisis inicial en main.py

TIEMPO_VELA = 300        # 5 minutos
CANTIDAD_VELAS = 150     # Más velas para mejor análisis IA
MONTO = 1.0
DURACION = 1              # minutos de duración de la operación
MODO_REAL = False
MAX_OPERACIONES_POR_DIA = 30
MAX_PERDIDA_DIARIA = 10.0
MIN_CONFIANZA_IA = 0.0   # TEMPORAL: para probar que el bot opera

# =============================================
# OTROS
# =============================================
ARCHIVO_MEMORIA_IA = os.path.join("data", "ia_memoria.json")
CACHE_DISPONIBILIDAD_SEGUNDOS = 300
# =============================================
# MODO APRENDIZAJE (SOLO PARA ENTRENAR LA IA)
# =============================================
# True  → El bot opera siempre en DEMO para que la IA acumule datos rápido
# False → Modo normal, solo opera con señales claras y confianza >= MIN_CONFIANZA_IA
# ⚠️ NUNCA usar MODO_APRENDIZAJE = True con MODO_REAL = True
MODO_APRENDIZAJE = True

# Duración temporal para aprender rápido (1 minuto)
# Cuando tengas 50+ patrones, ponlo de vuelta en 5
DURACION = 1