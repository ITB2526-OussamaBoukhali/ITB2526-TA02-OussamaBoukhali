import xml.etree.ElementTree as ET
import os
import time
import re
from collections import Counter

# Ruta al XML
xml_file = os.path.join(os.path.dirname(__file__), "incidencies.xml")

# Función para detectar palabras válidas
def es_palabra_valida(texto):
    if not texto:
        return False
    if not re.search(r"[aeiouáéíóú]", texto.lower()):
        return False
    if re.fullmatch(r"(.)\1{2,}", texto):  # ej: "aaaaaa", "11111"
        return False
    if re.fullmatch(r"[^\w]+", texto):     # ej: "<<<<", "////"
        return False
    return True

# Función para colorear urgencia
def colorear_urgencia(urgencia):
    colores = {
        "Alta": "\033[91mAlta\033[0m",       # rojo
        "Mitjana": "\033[93mMitjana\033[0m", # amarillo
        "Baixa": "\033[94mBaixa\033[0m"      # azul
    }
    return colores.get(urgencia, urgencia or "[sin urgencia]")

# Procesar incidencias
def procesar_incidencias():
    incidencias_filtradas = []
    total_registros = 0
    incorrectas = 0
    estadisticas_urgencia = Counter()

    if not os.path.exists(xml_file):
        print(f"❌ Archivo XML no encontrado: {xml_file}")
        return [], 0, 0, estadisticas_urgencia

    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError as e:
        print("❌ Error al parsear el XML:", e)
        return [], 0, 0, estadisticas_urgencia

    for i, reg in enumerate(root.findall("Registro"), start=1):
        total_registros += 1
        tipo = reg.findtext("Tipus_dincidencia_exemple_maquinari_programari_xarxa_correu_electronic_impressores_acces_a_sistemes_seguretat", "").strip()
        urgencia = reg.findtext("Nivell_durgencia_", "").strip()
        fecha = reg.findtext("Data_dincidencia", "").strip()
        descripcion = reg.findtext("Descripcio_detallada_del_problema", "").strip()

        # Filtro de fechas absurdas
        if fecha:
            try:
                anio = int(fecha.split("-")[0])
                if anio < 2020 or anio > 2030:
                    incorrectas += 1
                    continue
            except ValueError:
                incorrectas += 1
                continue

        # Filtro de textos largos (>200 caracteres)
        if descripcion and len(descripcion) > 200:
            incorrectas += 1
            continue

        # Filtro de palabras sin sentido
        if tipo and not es_palabra_valida(tipo):
            incorrectas += 1
            continue
        if descripcion and not es_palabra_valida(descripcion):
            incorrectas += 1
            continue

        if not tipo and not urgencia and not fecha and not descripcion:
            incorrectas += 1
            continue

        incidencias_filtradas.append({
            "id": i,
            "fecha": fecha or "[sin fecha]",
            "tipo": tipo or "[sin tipo]",
            "urgencia": urgencia,
            "descripcion": descripcion or "[sin descripción]"
        })

        if urgencia:
            estadisticas_urgencia[urgencia] += 1

    return incidencias_filtradas, total_registros, incorrectas, estadisticas_urgencia

# Mostrar estadísticas
def mostrar_estadisticas(incidencias, total_registros, incorrectas, estadisticas_urgencia):
    correctas = len(incidencias)
    porcentaje_correctas = (correctas / total_registros) * 100 if total_registros else 0
    porcentaje_incorrectas = (incorrectas / total_registros) * 100 if total_registros else 0

    print(f"\n✅ Total incidencias procesadas: {correctas}")
    print(f"❌ Total incidencias descartadas: {incorrectas}")
    print(f"📊 Porcentaje correctas: {porcentaje_correctas:.2f}%")
    print(f"📊 Porcentaje incorrectas: {porcentaje_incorrectas:.2f}%")

    print("\n📊 Estadísticas de urgencias:")
    for nivel in ["Alta", "Mitjana", "Baixa"]:
        cantidad = estadisticas_urgencia.get(nivel, 0)
        porcentaje = (cantidad / correctas * 100) if correctas else 0
        print(f"  {colorear_urgencia(nivel)}: {cantidad} ({porcentaje:.2f}%)")

# --- MENÚ PRINCIPAL ---
if __name__ == "__main__":
    incidencias, total, incorrectas, estad_urgencia = procesar_incidencias()

    if not incidencias and total == 0 and incorrectas == 0:
        print("⚠️ No se puede continuar sin el archivo XML.")
    else:
        while True:
            print("\n📌 Menú principal")
            print("1. Ver datos de incidencias (tabla)")
            print("2. Ver estadísticas")
            print("3. Salir")

            opcion = input("\n👉 Elige una opción (1, 2 o 3): ")

            if opcion == "1":
                # Mostrar tabla
                print("\n📋 Incidencias (formato tabla):")
                print(f"{'ID':<5}{'Fecha':<20}{'Tipo':<30}{'Urgencia':<20}{'Descripción':<80}")
                print("-" * 155)
                for inc in incidencias:
                    urgencia_coloreada = colorear_urgencia(inc['urgencia'])
                    print(f"{inc['id']:<5}{inc['fecha']:<20}{inc['tipo']:<30}{urgencia_coloreada:<20}{inc['descripcion'][:80]:<80}")
            elif opcion == "2":
                mostrar_estadisticas(incidencias, total, incorrectas, estad_urgencia)
            elif opcion == "3":
                print("👋 Saliendo del programa...")
                break
            