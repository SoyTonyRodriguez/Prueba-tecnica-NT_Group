# Proyecto: Prueba Técnica - NT Group

---

# Uso con Docker
> **Requisitos**  
> * Docker 20.10 o superior  
> * Docker Compose v2+

1. **Construir las imágenes**

   ```bash
   docker compose build
   ```

2. **Levantar contenedores (MongoDB + mongo-express + app)**

    ```bash
    docker compose up -d        # -d = segundo plano
   ```

3. **Ejecutar cualquier comando del script sin modificar el compose**

    ```bash
    # Cargar un CSV (sobrescribe datos)
    docker compose run --rm app \
    python main.py --load /data/data_prueba_tecnica.csv

    # Transformar a 'charges' y 'companies'
    docker compose run --rm app \
    python main.py --transforms

    # Mostrar la vista agregada
    docker compose run --rm app \
    python main.py --view

    # Exportar a CSV (crea ./data/salida.csv) el archivo se mostrara en la carpeta data, en el host
    docker compose run --rm app \
    python main.py --extract /data/salida.csv

    # Uso de la API
    docker compose run --rm app \
    python main.py --api 27
     ```

4. **Acceder a la base de datos**

    Acceder a http://localhost:8080/

    Ingresar las credenciales:
    - user
    - password

### ¿Por qué se incluyó mongo-express?
- **Inspección inmediata de datos**. Permite verificar que las colecciones (raw_data, charges, companies) se poblaron correctamente sin instalar software extra.
- **100 % en contenedores**. La app se levanta con un solo docker compose up.
- **Lectura y edición rapidas**
- **Alternativa a Compass**

En el uso local, se utilizo compass para verificar el estado de la base de datos

# Instalación (Local)

1. **Clonar el repositorio o descargar los archivos.**
2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```


# Uso

### Descomentar la linea de codigo en el archivo main.py
   ```python
    # Conexion a MongoDB (Docker)
    client = MongoClient('mongodb://admin:password@ntg_mongo:27017/')

    # Conexion a MongoDB (Local)
    # client = MongoClient('mongodb://localhost:27017/')
   ```


### 1. Cargar datos del CSV a MongoDB
```bash
python main.py --load data_prueba_tecnica.csv
```

### 2. Extraer datos a un nuevo CSV
```bash
python main.py --extract salida.csv
```

### 3. Transformar datos a las colecciones `charges` y `companies`
```bash
python main.py --transform
```

### 4. Crear vista agregada de montos por día y compañía
```bash
python main.py --view
```

### 5. Ejecutar la API de números naturales (extraer un número)
```bash
python main.py --api <numero>
```
Ejemplo:
```bash
python main.py --api 7
```

---

# Diagrama Base de Datos (MongoDB)

```
+------------------+              +----------------+
|    companies     |              |     charges     |
+------------------+              +----------------+
| _id (company_id) |<------------ | company_id      |
| company_name     |              | company_name    |
+------------------+              | amount          |
                                  | status          |
                                  | created_at      |
                                  | updated_at      |
                                  +----------------+
```

- `charges.company_id` hace referencia a `companies._id` (relación lógica).

---

# Comentarios

- **Base de datos elegida:** MongoDB, debido a su flexibilidad para esquemas semi-estructurados.
- **Formato de extracción:** CSV, por su simplicidad y compatibilidad.
- **Transformaciones:** Conversión de fechas a timestamps, ajuste de campos numéricos, creación de esquema relacional lógico.
- **Reto:** Manejo de datos nulos y formatos de fecha inconsistentes.

---