# Proyecto: Prueba Técnica - NT Group
# Sección 1: Procesamiento y transferencia de datos

import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import argparse
import re

# Conexion a MongoDB (Docker)
client = MongoClient('mongodb://admin:password@ntg_mongo:27017/')

# Conexion a MongoDB (Local)
# client = MongoClient('mongodb://localhost:27017/')

db = client['ntgroup_db']

# --- Parte 1: Carga de Informacion ---

def is_bad_name(name):
    bad_values = ["", "NaN", "nan", None]
    return name in bad_values

# --- Helpers de limpieza ---
def clean_company_id(cid: str):
    """Devuelve un company_id saneado o None si no es válido."""
    if pd.isna(cid):
        return None
    cid = str(cid).strip().lower()
    cid = cid.replace(" ", "")
    # IDs inválidos: vacíos, contienen caracteres no hexadecimales o '*'
    if cid == "" or "*" in cid or not re.fullmatch(r"[0-9a-f]+", cid):
        return None
    return cid


def clean_company_name(name: str):
    """Normaliza company_name corrigiendo espacios y capitalización.
    Devuelve None si no se puede limpiar."""
    if pd.isna(name):
        return None
    name = str(name).strip()
    name = re.sub(r"\s+", " ", name)  # colapsa espacios múltiples
    if name == "" or re.fullmatch(r"[0-9\\W_]+", name):  # solo dígitos o símbolos
        return None
    return name.title()


def load_data(csv_path):
    """Carga el CSV, limpia company_id y name.
    - Reemplaza nombres corruptos por uno válido de la misma company_id o 'Unknown Company'.
    - Descarta únicamente registros sin company_id utilizable.
    - Guarda los datos resultantes en la colección 'raw_data'."""
    df = pd.read_csv(csv_path)

    # Limpieza inicial de columnas clave
    df['company_id'] = df['company_id'].apply(clean_company_id)
    df['name'] = df['name'].apply(clean_company_name)

    # Diccionario temporal con el primer nombre válido encontrado por company_id
    good_names = {}
    for cid, cname in zip(df['company_id'], df['name']):
        if cid and cname:
            good_names.setdefault(cid, cname)

    # Construcción de registros finales
    records = []
    for _, row in df.iterrows():
        cid = row['company_id']
        if cid is None:
            # No es posible procesar registros sin identificador
            continue

        cname = row['name'] or good_names.get(cid, 'Unknown Company')
        created = row['created_at'] if 'created_at' in row else 'Unknown Date'
        row_dict = row.to_dict()
        row_dict['name'] = cname  # asegura nombre reparado
        row_dict['created_at'] = created  # asegura fecha reparada
        records.append(row_dict)

    # Persistencia en MongoDB
    db.raw_data.drop()
    if records:
        db.raw_data.insert_many(records)
    print(f"Datos cargados, {len(records)} registros procesados y corregidos en 'raw_data'.")

# --- Parte 2: Extraccion ---

def extract_data(output_csv):
    data = list(db.raw_data.find({}, {'_id': 0}))
    df = pd.DataFrame(data)
    df.to_csv(output_csv, index=False)
    print(f"Datos extraidos a {output_csv}.")

# --- Parte 3: Transformacion ---

def parse_date(date_str):
    if pd.isna(date_str):
        return None
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def transform_data():
    raw_data = db.raw_data.find()
    charges = []
    companies = {}

    for record in raw_data:
        company_id = record.get('company_id')
        name = record.get('name')

        if not isinstance(company_id, str):
            continue

        if company_id not in companies:
            companies[company_id] = name

        charges.append({
            'company_name': name,
            'company_id': company_id,
            'amount': float(record.get('amount', 0)),
            'status': record.get('status', 'unknown'),
            'created_at': parse_date(record.get('created_at')),
            'updated_at': parse_date(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        })

    db.charges.drop()
    db.companies.drop()

    if charges:
        db.charges.insert_many(charges)
    if companies:
        db.companies.insert_many([
            {'id': cid, 'company_name': cname} for cid, cname in companies.items()
        ])

    print("Transformación completa: colecciones 'charges' y 'companies' actualizadas.")

# --- Parte 4: Vista simulada (Aggregation) ---
def create_view():
    pipeline = [
        {
            '$group': {
                '_id': {
                    'date': {
                        '$cond': [
                            { '$ne': ['$created_at', None] },
                            { '$dateToString': { 'format': '%Y-%m-%d', 'date': '$created_at' } },
                            'Sin fecha'
                        ]
                    },
                    'company_name': '$company_name'
                },
                'total_amount': { '$sum': '$amount' }
            }
        },
        { '$sort': { '_id.date': 1, '_id.company_name': 1 } }
    ]

    result = db.charges.aggregate(pipeline)
    print("\nMonto total transaccionado por dia y compañía:\n")
    for r in result:
        print(r['_id']['date'], '-', r['_id']['company_name'], ':', r['total_amount'])

# --- Sección 2: Clase API para números naturales ---

class NaturalNumbersSet:
    def __init__(self):
        self.numbers = set(range(1, 101))

    def extract(self, number):
        if not (1 <= number <= 100):
            raise ValueError("El número debe ser entre 1 y 100.")
        self.numbers.remove(number)

    def find_missing_number(self):
        total_sum = 5050  # Sumatoria de 1 a 100
        current_sum = sum(self.numbers)
        return total_sum - current_sum

# --- Ejecución vía comandos ---

def main():
    parser = argparse.ArgumentParser(description='Prueba técnica NT Group')
    parser.add_argument('--load', help='Ruta CSV para cargar datos')
    parser.add_argument('--extract', help='Ruta para exportar CSV')
    parser.add_argument('--transform', action='store_true', help='Transformar datos')
    parser.add_argument('--view', action='store_true', help='Mostrar vista agregada')
    parser.add_argument('--api', type=int, help='Número a extraer del conjunto de naturales (1-100)')

    args = parser.parse_args()

    if args.load:
        load_data(args.load)
    if args.extract:
        extract_data(args.extract)
    if args.transform:
        transform_data()
    if args.view:
        create_view()
    if args.api is not None:
        ns = NaturalNumbersSet()
        ns.extract(args.api)
        missing = ns.find_missing_number()
        print(f"El número faltante es: {missing}")

if __name__ == '__main__':
    main()
