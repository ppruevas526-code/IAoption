"""Script para ver los nombres exactos de los activos disponibles."""
from iqoptionapi.stable_api import IQ_Option
import config

api = IQ_Option(config.EMAIL, config.PASSWORD)
api.connect()
print("✅ Conectado\n")

all_open = api.get_all_open_time()

for tipo in ['binary', 'turbo']:
    if tipo not in all_open:
        continue
    print(f"\n{'='*55}")
    print(f"📊 ACTIVOS {tipo.upper()} ABIERTOS AHORA")
    print(f"{'='*55}")
    abiertos = [a for a, v in all_open[tipo].items() if v.get('open')]
    print(f"Total abiertos: {len(abiertos)}")
    print()
    for a in sorted(abiertos):
        print(f"  • {a}")