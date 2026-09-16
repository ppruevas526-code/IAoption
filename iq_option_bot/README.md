# IQ Option AI Bot

Bot de trading para IQ Option con análisis técnico, detección de patrones
de velas y un selector de estrategias que aprende con el tiempo (memoria
de rendimiento por régimen de mercado).

## Estructura del proyecto

```
iq_option_bot/
├── main.py                     # Punto de entrada: conecta y corre el bucle principal
├── config.py                   # Configuración (lee credenciales desde .env)
├── .env.example                # Plantilla de variables de entorno
├── requirements.txt
├── core/                       # Lógica de análisis pura (sin tocar la API del broker)
│   ├── candle_analyzer.py      # Anatomía y patrones de velas
│   ├── indicators.py           # RSI, EMA, MACD, ADX, Bollinger, Estocástico...
│   ├── strategies.py           # Estrategias individuales (tendencia, ruptura, etc.)
│   ├── regime_detector.py      # Detecta tendencia / rango / volatilidad
│   ├── ai_selector.py          # Selector de estrategias con memoria de aciertos
│   └── analysis.py             # Une todo lo anterior para un activo
├── trading/                    # Todo lo que habla con la API de IQ Option
│   ├── broker.py               # Conexión, parches defensivos, reconexión
│   ├── availability.py         # Qué activos están operables ahora mismo
│   ├── operations_manager.py   # Ejecuta y hace seguimiento de órdenes en hilos
│   └── signal_counter.py       # Estadísticas de señales y operaciones
├── utils/
│   └── errors.py                # Traduce errores de la API a mensajes legibles
└── data/
    └── ia_memoria.json          # Se genera solo: memoria de aprendizaje de la IA
```

## Instalación

```bash
pip install -r requirements.txt
cp .env.example .env
# Edita .env con tu correo y contraseña de IQ Option
```

## Uso

```bash
python main.py
```

Por defecto corre en modo **DEMO** (`MODO_REAL = False` en `config.py`).
Cambia los activos, montos y umbrales de confianza directamente en
`config.py`.

## Notas de seguridad

- Las credenciales ya no están escritas en el código: se leen desde `.env`,
  que está incluido en `.gitignore` para que nunca se suba a un repositorio.
- `data/ia_memoria.json` se genera en tiempo de ejecución y tampoco se versiona.
