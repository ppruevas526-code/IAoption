"""Conexión a IQ Option y parches defensivos contra bugs conocidos de la librería."""
import sys
import time
import threading

from iqoptionapi.stable_api import IQ_Option


def conectar(email, password, modo_real=False):
    """Conecta a IQ Option, ajusta el tipo de cuenta y devuelve (api, balance)."""
    print("\n🔌 Conectando a IQ Option...")

    api = IQ_Option(email, password)
    api.connect()

    if not api.check_connect():
        print("❌ Error de conexión.")
        sys.exit(1)

    balance = api.get_balance()
    if balance is None:
        print("❌ No se pudo obtener el saldo.")
        sys.exit(1)

    if not modo_real:
        api.change_balance('PRACTICE')
        print("💰 Modo DEMO activado")
    else:
        api.change_balance('REAL')
        print("⚠️ Modo REAL activado")

    balance = api.get_balance()
    print(f"✅ Conectado | Saldo: {balance:.2f} USD")

    return api, balance


def aplicar_parche_underlying_seguro(api, intentos=3, espera=1.0):
    """
    🩹 PARCHE DEFENSIVO: bug conocido de iqoptionapi.

    Un hilo interno de la librería (usado al pedir horarios de digitales)
    a veces recibe None del servidor y hace data["underlying"] sin
    validar, reventando con TypeError: 'NoneType' object is not subscriptable.
    Envolvemos el método en la instancia para que nunca devuelva None
    y reintente un par de veces si la primera consulta falla.
    """
    original = api.get_digital_underlying_list_data

    def _seguro():
        for intento in range(1, intentos + 1):
            try:
                data = original()
            except Exception as e:
                print(f"⚠️ Intento {intento}/{intentos}: error consultando subyacentes digitales: {e}")
                data = None

            if data and isinstance(data, dict) and data.get('underlying') is not None:
                return data

            if intento < intentos:
                time.sleep(espera)

        print("⚠️ No se pudo obtener la lista de subyacentes digitales tras varios intentos; "
              "se devuelve lista vacía para evitar que el bot se caiga.")
        return {"underlying": []}

    api.get_digital_underlying_list_data = _seguro


def instalar_excepthook_amigable():
    """Si algún hilo interno de la librería revienta por el bug conocido,
    que se vea como un aviso claro y no como una traza intimidante."""
    original = threading.excepthook

    def _amigable(args):
        if args.exc_type is TypeError and 'NoneType' in str(args.exc_value):
            print("⚠️ Hipo de conexión con IQ Option (hilo interno de la librería). "
                  "El bot sigue corriendo; si se repite mucho, revisa tu conexión a internet.")
            return
        original(args)

    threading.excepthook = _amigable


def verificar_reconectar(api):
    """Verifica la conexión y reintenta reconectar si se perdió.
    Devuelve True si la conexión está (o quedó) activa."""
    if api.check_connect():
        return True

    print("🔌 Conexión perdida, reconectando...")
    api.connect()
    time.sleep(2)
    if not api.check_connect():
        print("⚠️ No se pudo reconectar, se reintenta en el próximo ciclo.")
        return False

    print("✅ Reconectado")
    return True
