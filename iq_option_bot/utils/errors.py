"""
Traduce las respuestas crípticas de la API (dicts con 'code'/'message')
a un texto entendible, con el motivo probable.
"""

_TRADUCCIONES_ERROR = {
    'invalid instrument': (
        'el instrumento no está disponible para operar en este momento '
        '(mercado cerrado o sin opciones digitales habilitadas para esta cuenta)'
    ),
    'invalid amount': 'el monto configurado en MONTO no es válido para este instrumento',
    'not enough money': 'no hay saldo suficiente en la cuenta para esta operación',
    'active is suspended': 'este instrumento está suspendido temporalmente por el broker',
}


def formatear_error_orden(respuesta):
    """Convierte la respuesta de error de buy_digital_spot_v2 en un
    mensaje legible. Acepta tanto dicts {'code':..,'message':..} como
    strings u otros tipos, por si la librería cambia el formato."""
    if isinstance(respuesta, dict):
        codigo = respuesta.get('code', 'desconocido')
        mensaje_original = str(respuesta.get('message', '')).strip()
        explicacion = _TRADUCCIONES_ERROR.get(
            mensaje_original.lower(), mensaje_original or 'motivo no especificado'
        )
        return f"{explicacion} (código interno: {codigo})"
    return str(respuesta)
