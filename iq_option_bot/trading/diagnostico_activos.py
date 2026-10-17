from iqoptionapi.stable_api import IQ_Option
import config

api = IQ_Option(config.EMAIL, config.PASSWORD)
api.connect()
print("✅ Conectado\n")

all_open = api.get_all_open_time()

# Ver qué categorías devuelve la API
print("📋 Categorías disponibles:", list(all_open.keys()))
print()

for categoria in ['digital', 'binary', 'turbo']:
    if categoria not in all_open:
        continue
    abiertos = [a for a, v in all_open[categoria].items() if v.get('open')]
    print(f"🟢 {categoria.upper()}: {len(abiertos)} activos abiertos")
    for a in sorted(abiertos)[:15]:  # primeros 15
        print(f"   • {a}")
    print()

# Verificar activos específicos de tu config
print("🔍 Verificando tus activos configurados:")
for activo in config.ACTIVOS_DISPONIBLES[:20]:
    estado = "❌"
    for cat in ['digital', 'binary', 'turbo']:
        if cat in all_open and activo in all_open[cat]:
            if all_open[cat][activo].get('open'):
                estado = f"✅ ({cat})"
                break
    print(f"   {estado} {activo}")