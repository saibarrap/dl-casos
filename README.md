# DL Casos — Sistema de gestion de casos de RC Medica (MVP Sprint 1)

Sistema de gestion de casos de Responsabilidad Civil Medica para **DL Abogados**.
Reemplaza un Excel compartido, aportando integridad de datos, deteccion de
duplicados, control de permisos por rol y trazabilidad. La unica interfaz es el
**Django admin personalizado**.

- **Stack:** Python 3.12, Django 5.2 LTS, MySQL 8.0 (InnoDB).
- **Idioma:** espanol. **Zona horaria:** America/Bogota.
- **Alcance Sprint 1:** HU-01 a HU-05 (login seguro, roles/permisos, registro de
  casos, duplicados/reingresos, busqueda/filtros/paginacion).
- **Fuera de alcance:** importacion de Excel, historial de cambios, transiciones
  de estado, enlaces a SharePoint y a Notion.

> Datos reales confidenciales (historias clinicas): en desarrollo y pruebas use
> **solo datos ficticios**.

## Requisitos previos

- Python 3.12 (funciona tambien con 3.11).
- Docker (para MySQL 8.0).

## Puesta en marcha

### 1. Variables de entorno

```bash
cp .env.example .env
# edite .env y defina SECRET_KEY, DB_PASSWORD, SEED_PASSWORD, etc.
```

### 2. Levantar MySQL 8.0 con Docker

```bash
docker compose up -d
# espera a que el contenedor este "healthy"
docker compose ps
```

### 3. Entorno virtual e instalacion de dependencias

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> Si `mysqlclient` falla al instalar en Windows, use PyMySQL:
> ```bash
> pip install PyMySQL
> ```
> y descomente las dos lineas de `config/__init__.py`.

### 4. Migraciones

```bash
python manage.py migrate
```

Las reglas de integridad quedan en la base de datos. Puede verificarlas con:

```sql
SHOW CREATE TABLE casos_caso;
-- debe incluir UNIQUE KEY uniq_siniestro_aseguradora (siniestro_normalizado, aseguradora)
-- y el CHECK ck_caso_estado
```

### 5. Datos de arranque

```bash
# Grupos (roles) + usuarios demo. La contrasena viene de SEED_PASSWORD (.env).
python manage.py seed_roles

# Datos ficticios para pruebas de rendimiento (p. ej. 4000 casos):
python manage.py seed_demo_data --cantidad 4000
```

Usuarios demo creados por `seed_roles` (todos con la contrasena de `SEED_PASSWORD`):

| Usuario | Rol |
|---|---|
| `admin` | superusuario |
| `coordinacion` | Coordinacion |
| `asistente` | Asistente |
| `abogado1` | Abogado |
| `consulta` | Consulta |

### 6. Ejecutar el servidor

```bash
python manage.py runserver
# Admin en http://127.0.0.1:8000/admin/
```

## Pruebas

```bash
python manage.py test
```

Las pruebas estan escritas para **MySQL** (una o mas por cada criterio de
aceptacion; el nombre del metodo incluye el ID, p. ej. `test_ca_04_1_...`). La
tabla criterio -> prueba esta en [`docs/matriz_ca.md`](docs/matriz_ca.md).

Para ejecutar las pruebas, la base de datos de test tambien se crea en MySQL, por
lo que el contenedor debe estar arriba y el usuario de BD debe poder crear la
base de datos de pruebas (`test_<DB_NAME>`). Si usa el usuario de aplicacion sin
permiso para crear bases, ejecute las pruebas con un usuario con privilegios o
otorgue `CREATE` sobre `test_dl_casos`.

> **Importante:** no se cambia a SQLite para que las pruebas pasen. Si no hay
> MySQL disponible, las pruebas dependientes del motor (rendimiento con >3.700
> casos y la garantia UNIQUE a nivel de BD) quedan escritas pero no ejecutadas.

## Estructura

```
config/   # proyecto Django (settings, urls, wsgi/asgi)
casos/    # app de dominio: models, admin, forms, normalizacion, permisos,
          # management/commands (seed_roles, seed_demo_data), tests
docs/     # matriz_ca.md (criterio -> prueba)
```

## Modelo de datos (resumen)

- **Aseguradora**: `nombre` (unico), `activa`.
- **Caso**: `numero_siniestro`, `siniestro_normalizado` (calculado), `aseguradora`
  (FK), `numero_poliza`, `fecha_recepcion`, `asegurado`, `estado`
  (REGISTRADO/ASIGNADO/EN_ANALISIS/ENVIADO_ASEGURADORA/CERRADO, default
  REGISTRADO), `abogado_asignado` (FK opcional), `observaciones`, auditoria
  (`creado_por`, `creado_en`, `actualizado_por`, `actualizado_en`).
  Restricciones en BD: `UNIQUE(siniestro_normalizado, aseguradora)` y `CHECK` del
  estado.
- **Reingreso**: `caso` (FK), `fecha_reingreso`, `trae_documentos_nuevos`,
  `observaciones`, `registrado_por`, `creado_en`.

Los campos son provisionales y se ajustaran a las columnas reales del Excel.

## Disclaimer
El contenido presente en este repositorio fue generado por IA para fines académicos. Los agentes utilizados fueron Claude de Anthropic y Kiro App Web. La gestión, testeo y revisión de los documentos fue realizada por el equipo de trabajo.
