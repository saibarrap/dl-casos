# Tecnología
- Python 3.12 y Django (versión LTS más reciente). La interfaz es el Django admin personalizado; NO construir un front aparte.
- MySQL 8.0 con InnoDB. Las reglas de integridad van en la BASE DE DATOS (NOT NULL, UNIQUE, CHECK, FK), no solo en el código.
- Cliente: mysqlclient (si falla la instalación en Windows, usar PyMySQL).
- Configuración por variables de entorno (.env). Nunca credenciales en el repositorio.
- Pruebas con el test runner de Django. Cada criterio de aceptación tiene al menos una prueba cuyo nombre incluye su ID (ej. test_ca_04_1_...).
- MySQL corre en Docker; la app corre localmente en un venv.
