import xml.etree.ElementTree as ET
import os
import re
import json
from collections import Counter

# Rutas
xml_file = os.path.join(os.path.dirname(__file__), "incidencies.xml")
json_file = os.path.join(os.path.dirname(__file__), "incidencies.json")

# --- Funciones auxiliares ---
def es_palabra_valida(texto):
    if not texto:
        return False
    if not re.search(r"[aeiouáéíóú]", texto.lower()):
        return False
    if re.fullmatch(r"(.)\1{2,}", texto):
        return False
    if re.fullmatch(r"[^\w]+", texto):
        return False
    return True

def colorear_urgencia(urgencia):
    colores = {
        "Alta": "\033[91mAlta\033[0m",
        "Media": "\033[93mMedia\033[0m",
        "Baja": "\033[94mBaja\033[0m"
    }
    return colores.get(urgencia, urgencia or "[sin urgencia]")

# --- Procesar incidencias ---
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
        tipo = reg.findtext("Tipo_incidencia", "").strip()
        urgencia = reg.findtext("Nivel_urgencia", "").strip()
        fecha = reg.findtext("Fecha_incidencia", "").strip()
        descripcion = reg.findtext("Descripcion_problema", "").strip()

        # Filtros
        if fecha:
            try:
                anio = int(fecha.split("-")[0])
                if anio < 2020 or anio > 2030:
                    incorrectas += 1
                    continue
            except ValueError:
                incorrectas += 1
                continue

        if descripcion and len(descripcion) > 200:
            incorrectas += 1
            continue

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

# --- Guardar en JSON con gestión ---
def guardar_json(incidencias):
    if not os.path.exists(json_file):
        # Crear nuevo archivo
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(incidencias, f, ensure_ascii=False, indent=4)
        print(f"\n\033[92m✅ Archivo JSON creado con {len(incidencias)} incidencias nuevas\033[0m")
    else:
        print("\n⚠️ El archivo JSON ya existe.")
        print("1. Sobrescribirlo (borra el contenido anterior)")
        print("2. Añadir las nuevas incidencias (evitando duplicados)")
        opcion = input("👉 Elige una opción (1 o 2): ")

        if opcion == "1":
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(incidencias, f, ensure_ascii=False, indent=4)
            print(f"\n\033[92m✅ Archivo JSON sobrescrito con {len(incidencias)} incidencias nuevas\033[0m")

        elif opcion == "2":
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    existentes = json.load(f)
            except Exception:
                existentes = []

            # Evitar duplicados por ID
            ids_existentes = {inc["id"] for inc in existentes}
            nuevas = [inc for inc in incidencias if inc["id"] not in ids_existentes]
            combinadas = existentes + nuevas

            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(combinadas, f, ensure_ascii=False, indent=4)
            print(f"\n\033[92m✅ Se han añadido {len(nuevas)} incidencias nuevas al JSON")

        else:
            print("❌ Opción no válida. No se ha modificado el archivo JSON.")

# --- Ejecución principal ---
if __name__ == "__main__":
    incidencias, total, incorrectas, estad_urgencia = procesar_incidencias()

    if not incidencias and total == 0 and incorrectas == 0:
        print("⚠️ No se puede continuar sin el archivo XML.")
    else:
        # Mostrar estadísticas
        print(f"\n✅ Total incidencias correctas: {len(incidencias)}")
        print(f"❌ Total incidencias descartadas: {incorrectas}")
        guardar_json(incidencias)
