"""
Bot de trading IA para IQ Option — punto de entrada.
VERSIÓN FLEXIBLE con IA agresiva.
"""
import sys
import time
import random

import config

def tipo_activo(activo):
    """Devuelve 'OTC' o 'NORMAL' según el nombre del activo."""
    if activo.upper().endswith("-OTC"):
        return "🟡 OTC"
    return "🔵 NORMAL"

def verificar_dependencias():
    try:
        import pandas  # noqa: F401
        import numpy  # noqa: F401
        print("✅ Pandas y Numpy instalados correctamente")
    except ImportError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    try:
        from iqoptionapi.stable_api import IQ_Option  # noqa: F401
        print("✅ IQ Option API instalada correctamente")
    except ImportError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    try:
        from sklearn.ensemble import RandomForestClassifier  # noqa: F401
        print("✅ Scikit-learn disponible (IA activada)")
    except ImportError:
        print("⚠️ Scikit-learn no instalado. Usando IA interna simplificada.")

def pedir_direccion(activo, senal_sugerida):
    sugerida = "CALL" if senal_sugerida == "CALL" else "PUT"
    print("=" * 55)
    print(f"🎯 DIRECCIÓN DE LA OPERACIÓN PARA {activo}")
    print("=" * 55)
    print(f"  🤖 Sugerencia de la IA: {sugerida}")
    print()
    print("  1. 📈 CALL  (subida / compra)")
    print("  2. 📉 PUT   (bajada / venta)")
    print(f"  3. 🤖 Usar la sugerencia de la IA ({sugerida})")
    print("  4. 🎲 Aleatorio (deja que el bot decida)")

    while True:
        opcion = input("\n👉 Elige la dirección (1/2/3/4): ").strip()
        if opcion == "1":
            print("✅ Dirección: CALL (subida)\n")
            return "call"
        elif opcion == "2":
            print("✅ Dirección: PUT (bajada)\n")
            return "put"
        elif opcion == "3":
            print(f"✅ Dirección: {sugerida} (sugerencia IA)\n")
            return sugerida.lower()
        elif opcion == "4":
            aleatoria = random.choice(["call", "put"])
            print(f"🎲 Dirección aleatoria: {aleatoria.upper()}\n")
            return aleatoria
        else:
            print("❌ Opción inválida. Ingresa 1, 2, 3 o 4.")

def analizar_y_elegir(api, selector_ia, disponibilidad):
    from core.analysis import analizar_activo

    print("\n" + "=" * 65)
    print("🔎 ANALIZANDO ACTIVOS DISPONIBLES...")
    print("=" * 65)

    activos_operables = disponibilidad.obtener()
    if activos_operables:
        print(f"✅ Operables ahora: {len(activos_operables)} activos")
    else:
        print("⚠️ Ningún activo reportado como operable (se ignorará por config)")

    resultados = []
    for activo in config.ACTIVOS_DISPONIBLES:
        try:
            velas = api.get_candles(
                activo, config.TIEMPO_VELA, config.CANTIDAD_VELAS, time.time()
            )
            if not velas or len(velas) < 30:
                continue

            resultado = analizar_activo(activo, velas, selector_ia)
            resultado['operable'] = activo in activos_operables or config.IGNORAR_DISPONIBILIDAD
            resultado['tipo'] = tipo_activo(activo)
            resultados.append(resultado)

            estado = "✅" if resultado['operable'] else "🚫"
            print(
                f"{resultado['tipo']} | 📊 {activo} | {resultado['señal']} "
                f"({resultado['confianza']*100:.0f}%) | {resultado['regimen']} | {estado}"
            )
        except Exception:
            continue

    if not resultados:
        print("❌ No se pudo analizar ningún activo. Saliendo.")
        sys.exit(1)

    # Ordenar por confianza
    candidatos = [r for r in resultados if r['operable']]
    candidatos.sort(key=lambda x: x['confianza'], reverse=True)

    print("\n" + "=" * 65)
    print("🎯 RANKING DE OPORTUNIDADES")
    print("=" * 65)

    if not candidatos:
        print("⏸️ Ningún activo operable.")
        return config.ACTIVOS_DISPONIBLES, None

    # Mostrar top 10
    for i, r in enumerate(candidatos[:10], 1):
        print(
            f"  {i}. {r['tipo']} | {r['activo']} → {r['señal']} "
            f"(confianza {r['confianza']*100:.0f}%) | {r['regimen']}"
        )

    print(f"  {len(candidatos)+1}. 🤖 Dejar que el bot elija automáticamente")
    print(f"  {len(candidatos)+2}. 👀 Vigilar todos sin operar")

    while True:
        try:
            opcion = input("\n👉 Elige el número de la opción a operar: ").strip()
            idx = int(opcion) - 1

            if 0 <= idx < len(candidatos):
                elegido = candidatos[idx]['activo']
                tipo = candidatos[idx]['tipo']
                print(f"\n✅ Has elegido operar: {elegido} [{tipo}]")
                direccion_forzada = pedir_direccion(elegido, candidatos[idx]['señal'])
                return [elegido], direccion_forzada

            elif idx == len(candidatos):
                elegido = candidatos[0]['activo']
                tipo = candidatos[0]['tipo']
                print(f"\n🤖 El bot operará automáticamente: {elegido} [{tipo}]\n")
                direccion_forzada = pedir_direccion(elegido, candidatos[0]['señal'])
                return [elegido], direccion_forzada

            elif idx == len(candidatos) + 1:
                print("👀 Modo vigilancia: se analizarán todos sin operar.\n")
                return config.ACTIVOS_DISPONIBLES, None

            else:
                print("❌ Número fuera de rango.")
        except ValueError:
            print("❌ Ingresa solo un número.")

def main():
    verificar_dependencias()

    if not config.EMAIL or not config.PASSWORD:
        print("\n❌ Faltan credenciales.")
        sys.exit(1)

    from trading import broker
    from trading.signal_counter import ContadorSenales
    from trading.availability import DisponibilidadInstrumentos
    from trading.operations_manager import GestorOperaciones
    from core.ai_selector import SelectorEstrategiaIA
    from core.analysis import analizar_activo  # noqa: F401

    api, balance = broker.conectar(config.EMAIL, config.PASSWORD, config.MODO_REAL)
    broker.aplicar_parche_underlying_seguro(api)
    broker.instalar_excepthook_amigable()

    contador = ContadorSenales()
    contador.actualizar_balance(balance)

    selector_ia = SelectorEstrategiaIA()
    print(f"🧠 IA cargada con {len(selector_ia.rendimiento)} patrones aprendidos")

    disponibilidad = DisponibilidadInstrumentos(
        api,
        config.ACTIVOS_DISPONIBLES,
        cache_segundos=config.CACHE_DISPONIBILIDAD_SEGUNDOS,
    )

    config.ACTIVOS, direccion_forzada = analizar_y_elegir(
        api, selector_ia, disponibilidad
    )

    gestor_operaciones = GestorOperaciones(
        api, contador, selector_ia,
        monto=config.MONTO, duracion=config.DURACION,
        on_instrumento_invalido=lambda activo: disponibilidad.obtener(forzar=True),
    )

    print(f"\n🚀 BOT IA INICIADO")
    print(f"📊 Activos en seguimiento: {', '.join(config.ACTIVOS)}")
    if direccion_forzada:
        print(f"🎯 Dirección forzada: {direccion_forzada.upper()}")
    if getattr(config, 'MODO_APRENDIZAJE', False):
        print(f"🎓 MODO APRENDIZAJE ACTIVADO — la IA aprenderá rápido (solo DEMO)")
    if getattr(config, 'IGNORAR_DISPONIBILIDAD', False):
        print(f"⚡ IGNORAR_DISPONIBILIDAD activo")
    print(f"⏱️ Vela: {config.TIEMPO_VELA}s | Duración op: {config.DURACION} min")
    print(f"🎯 Confianza mínima: {config.MIN_CONFIANZA_IA*100:.0f}%")
    print("⏳ Comenzando en 5 segundos... (Ctrl+C para detener)")
    time.sleep(5)

    detenido_por_limite = False
    ignorar_disp = getattr(config, 'IGNORAR_DISPONIBILIDAD', False)

    # =============================================
    # BUCLE PRINCIPAL
    # =============================================
    while True:
        try:
            if not broker.verificar_reconectar(api):
                time.sleep(5)
                continue

            activos_operables = disponibilidad.obtener()
            if activos_operables:
                print(f"✅ Operables ahora: {len(activos_operables)} activos")
            else:
                print("⚠️ Ningún activo reportado como operable (ignorado por config)")

            analisis_activos = []

            for activo in config.ACTIVOS:
                try:
                    velas = api.get_candles(
                        activo, config.TIEMPO_VELA, config.CANTIDAD_VELAS, time.time()
                    )
                    if not velas or len(velas) < 30:
                        print(f"⚠️ {activo}: pocas velas, saltando")
                        continue

                    resultado = analizar_activo(activo, velas, selector_ia)
                    analisis_activos.append(resultado)

                    hora = time.strftime('%H:%M:%S')
                    ocupado = (
                        " (operación en curso)"
                        if gestor_operaciones.esta_ocupado(activo)
                        else ""
                    )
                    print(
                        f"{tipo_activo(activo)} | 📊 {hora} | {activo} | {resultado['precio']:.5f} | "
                        f"{resultado['señal']} ({resultado['confianza']*100:.0f}%) | "
                        f"Régimen: {resultado['regimen']} | "
                        f"Estrategia: {resultado['estrategia']}{ocupado}"
                    )

                    contador.registrar_senal(
                        activo, resultado['señal'], resultado['precio'],
                        hora, resultado['regimen'], resultado['estrategia'],
                        resultado['confianza']
                    )
                except Exception as e:
                    print(f"❌ Error analizando {activo}: {e}")

            stats = contador.obtener_estadisticas()
            if stats['total_senales'] % 5 == 0 and stats['total_senales'] > 0:
                contador.mostrar_estadisticas()

            # =========================================================
            # 🔥 FILTRO FLEXIBLE CON IA (VERSIÓN MEJORADA)
            # =========================================================
            if getattr(config, 'MODO_APRENDIZAJE', False):
                # MODO APRENDIZAJE: incluye TODOS los activos, incluso ESPERAR
                oportunidades = [
                    a for a in analisis_activos
                    if not gestor_operaciones.esta_ocupado(a['activo'])
                    and (ignorar_disp or a['activo'] in activos_operables)
                ]

                # 🔥 La IA decide la dirección cuando hay ESPERAR
                for a in oportunidades:
                    if a['señal'] == 'ESPERAR':
                        if a.get('confianza', 0) >= getattr(config, 'CONFIANZA_IA_PARA_DECIDIR', 0.25):
                            # Usa el sesgo de la IA según régimen
                            if a.get('regimen') == 'tendencia_alcista':
                                a['señal'] = 'CALL'
                            elif a.get('regimen') == 'tendencia_bajista':
                                a['señal'] = 'PUT'
                            else:
                                a['señal'] = random.choice(['CALL', 'PUT'])
                        else:
                            a['señal'] = random.choice(['CALL', 'PUT'])

                        a['confianza'] = max(a.get('confianza', 0), 0.5)
                        a['estrategia'] = 'IA_APRENDIZAJE'

                oportunidades.sort(key=lambda x: x.get('confianza', 0), reverse=True)
                print(f"🎓 MODO APRENDIZAJE: {len(oportunidades)} oportunidades forzadas")

            else:
                # MODO NORMAL: respeta la confianza mínima
                oportunidades = [
                    a for a in analisis_activos
                    if a['señal'] in ('CALL', 'PUT')
                    and a['confianza'] >= config.MIN_CONFIANZA_IA
                    and not gestor_operaciones.esta_ocupado(a['activo'])
                    and (ignorar_disp or a['activo'] in activos_operables)
                ]

            # =========================================================
            # DEBUG - Ver por qué se filtran
            # =========================================================
            print(f"\n🔍 DEBUG DEL FILTRO:")
            print(f"   Analizados: {len(analisis_activos)}")
            print(f"   Operables (API): {len(activos_operables) if activos_operables else 0}")
            print(f"   IGNORAR_DISPONIBILIDAD: {ignorar_disp}")
            print(f"   MODO_APRENDIZAJE: {getattr(config, 'MODO_APRENDIZAJE', False)}")
            print(f"   MIN_CONFIANZA_IA: {config.MIN_CONFIANZA_IA}")
            print(f"   Oportunidades tras filtro: {len(oportunidades)}")

            # Bloqueadas por mercado
            bloqueadas_por_mercado = [
                a for a in analisis_activos
                if a['señal'] in ('CALL', 'PUT')
                and a['confianza'] >= config.MIN_CONFIANZA_IA
                and not ignorar_disp
                and a['activo'] not in activos_operables
            ]
            for b in bloqueadas_por_mercado:
                print(
                    f"⏭️ {b['activo']}: señal {b['señal']} "
                    f"({b['confianza']*100:.0f}%) válida pero mercado no confirmado."
                )

            if oportunidades:
                oportunidades.sort(key=lambda x: x['confianza'], reverse=True)

                if contador.limite_perdida_alcanzado():
                    print("⚠️ Límite de pérdida diaria alcanzado.")
                    detenido_por_limite = True
                elif contador.limite_operaciones_alcanzado():
                    print("⚠️ Límite de operaciones diarias alcanzado.")
                    detenido_por_limite = True
                else:
                    for op in oportunidades:
                        if (contador.limite_operaciones_alcanzado()
                                or contador.limite_perdida_alcanzado()):
                            break

                        if direccion_forzada:
                            direccion = direccion_forzada
                            print(f"\n🎯 OPORTUNIDAD: {op['activo']} → {direccion.upper()} (forzada)")
                        else:
                            direccion = "call" if op['señal'] == "CALL" else "put"
                            print(f"\n🎯 OPORTUNIDAD: {op['activo']} → {op['señal']} "
                                  f"(confianza {op['confianza']*100:.0f}%)")

                        contador.registrar_operacion_iniciada()
                        print(f"📤 Lanzando operación: {op['activo']} {direccion.upper()}")

                        gestor_operaciones.lanzar_operacion(
                            op['activo'], direccion, op['precio'],
                            op['regimen'], op['estrategia']
                        )
            else:
                print(f"⏸️ Sin oportunidades nuevas")

            if detenido_por_limite:
                print("🧭 Esperando a que cierren las operaciones abiertas...")
                gestor_operaciones.esperar_pendientes()
                break

            ahora = time.time()
            siguiente_cierre = ((ahora // config.TIEMPO_VELA) + 1) * config.TIEMPO_VELA
            espera = siguiente_cierre - ahora
            if espera > 0:
                print(f"⏳ Esperando {espera:.1f} segundos...\n")
                time.sleep(espera + 0.5)

        except KeyboardInterrupt:
            print("\n🛑 Bot detenido por el usuario")
            contador.mostrar_estadisticas()
            print("🧭 Esperando a que cierren las operaciones en curso...")
            try:
                gestor_operaciones.esperar_pendientes()
            except KeyboardInterrupt:
                print("⚠️ Saliendo sin esperar.")
            print(f"\n🧠 IA aprendió {len(selector_ia.rendimiento)} combinaciones")
            break
        except Exception as e:
            print(f"❌ ERROR: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()