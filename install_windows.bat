@echo off
echo ============================================
echo    Mi C::Crear archivo de configuracion
echo.
echo [INFO] Configurando variables de entorno...
if not exist ".env" (
    echo # Configuracion Mi ::Abrir archivo de configuracion
echo.
echo [INFO] El archivo .env ha sido configurado automaticamente con:
echo   - Conexion a base de datos Render
echo   - Variables de entorno completas  
echo   - Sistema hibrido habilitado
echo.
echo ¿Quieres revisar la configuracion? ^(Opcional^)
set /p revisar="Abrir archivo .env para revision? (s/n): "
if /i "%revisar%"=="s" (
    notepad .env
)as-K v3.1.0 - Sistema Hibrido > .env
    echo # ==================================================== >> .env
    echo. >> .env
    echo # Base de datos remota ^(Render^) - CONFIGURACION PRINCIPAL >> .env
    echo DATABASE_URL=postgresql://admin:wkxMvaYK9HZaSWCsMn2aZJA3EMC9wLNu@dpg-d13oam8dl3ps7392hfu0-a.oregon-postgres.render.com/chaskabd >> .env
    echo. >> .env
    echo # Configuracion individual ^(respaldo^) >> .env
    echo DB_HOST=dpg-d13oam8dl3ps7392hfu0-a.oregon-postgres.render.com >> .env
    echo DB_NAME=chaskabd >> .env
    echo DB_USER=admin >> .env
    echo DB_PASSWORD=wkxMvaYK9HZaSWCsMn2aZJA3EMC9wLNu >> .env
    echo DB_PORT=5432 >> .env
    echo. >> .env
    echo # Configuracion de aplicacion >> .env
    echo SECRET_KEY=bd5d56cac14e32603c3e26296d88f26d >> .env
    echo PORT=8501 >> .env
    echo PYTHON_VERSION=3.9 >> .env
    echo. >> .env
    echo # Sistema hibrido >> .env
    echo SYSTEM_NAME=Mi Chas-K >> .env
    echo SYSTEM_VERSION=3.1.0 >> .env
    echo DEBUG_MODE=false >> .env
)dor Automatico
echo    Sistema de Punto de Venta v3.0.0
echo ============================================
echo.

:: Verificar si Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado.
    echo.
    echo Por favor descarga e instala Python desde:
    echo https://www.python.org/downloads/
    echo.
    echo Asegurate de marcar "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
)

echo [OK] Python encontrado:
python --version

:: Crear directorio del proyecto si no existe
if not exist "Mi-Chas-K" (
    echo.
    echo [INFO] Creando directorio del proyecto...
    mkdir "Mi-Chas-K"
)

cd "Mi-Chas-K"

:: Descargar archivos del proyecto desde GitHub
echo.
echo [INFO] Descargando proyecto desde GitHub...

:: Opcion 1: Con git si esta disponible
git --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Usando Git para descargar...
    git clone https://github.com/ReapeRAlan/Mi-Chas-K.git .
) else (
    echo [INFO] Git no encontrado. Descargando ZIP...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/ReapeRAlan/Mi-Chas-K/archive/refs/heads/main.zip' -OutFile 'proyecto.zip'"
    powershell -Command "Expand-Archive -Path 'proyecto.zip' -DestinationPath '.' -Force"
    move "Mi-Chas-K-main\*" .
    rmdir /s /q "Mi-Chas-K-main"
    del "proyecto.zip"
)

:: Crear entorno virtual
echo.
echo [INFO] Creando entorno virtual...
python -m venv venv

:: Activar entorno virtual
echo [INFO] Activando entorno virtual...
call venv\Scripts\activate.bat

:: Actualizar pip
echo [INFO] Actualizando pip...
python -m pip install --upgrade pip

:: Instalar dependencias
echo [INFO] Instalando dependencias...
if exist "requirements_simple.txt" (
    pip install -r requirements_simple.txt
) else (
    echo [INFO] Instalando dependencias basicas...
    pip install streamlit psycopg2-binary pandas numpy requests python-dotenv reportlab pytz
)

:: Crear archivo de configuracion
echo.
echo [INFO] Configurando variables de entorno...
if not exist ".env" (
    echo # Configuracion Mi Chas-K v3.0.0 > .env
    echo # Base de datos remota ^(Render^) >> .env
    echo DATABASE_URL=tu_url_de_base_de_datos_aqui >> .env
    echo. >> .env
    echo # Configuracion local ^(solo si no usas DATABASE_URL^) >> .env
    echo DB_HOST=localhost >> .env
    echo DB_NAME=chaskabd >> .env
    echo DB_USER=admin >> .env
    echo DB_PASSWORD=tu_password >> .env
    echo DB_PORT=5432 >> .env
)

:: Crear directorio de datos
if not exist "data" (
    mkdir "data"
)

:: Crear script de inicio
echo @echo off > iniciar.bat
echo call venv\Scripts\activate.bat >> iniciar.bat
echo streamlit run app_hybrid.py --server.port 8501 --server.address localhost >> iniciar.bat
echo pause >> iniciar.bat

:: Crear script de inicio con menu
echo @echo off > menu.bat
echo title Mi Chas-K - Menu Principal >> menu.bat
echo :menu >> menu.bat
echo cls >> menu.bat
echo echo ================================================ >> menu.bat
echo echo    Mi Chas-K - Sistema de Punto de Venta >> menu.bat
echo echo    Version 3.0.0 - Modo Hibrido >> menu.bat
echo echo ================================================ >> menu.bat
echo echo. >> menu.bat
echo echo 1. Iniciar Sistema >> menu.bat
echo echo 2. Configurar Base de Datos >> menu.bat
echo echo 3. Ver Estado del Sistema >> menu.bat
echo echo 4. Actualizar Sistema >> menu.bat
echo echo 5. Salir >> menu.bat
echo echo. >> menu.bat
echo set /p opcion="Selecciona una opcion (1-5): " >> menu.bat
echo. >> menu.bat
echo if "%%opcion%%"=="1" goto iniciar >> menu.bat
echo if "%%opcion%%"=="2" goto configurar >> menu.bat
echo if "%%opcion%%"=="3" goto estado >> menu.bat
echo if "%%opcion%%"=="4" goto actualizar >> menu.bat
echo if "%%opcion%%"=="5" goto salir >> menu.bat
echo goto menu >> menu.bat
echo. >> menu.bat
echo :iniciar >> menu.bat
echo call venv\Scripts\activate.bat >> menu.bat
echo streamlit run app_hybrid.py --server.port 8501 --server.address localhost >> menu.bat
echo goto menu >> menu.bat
echo. >> menu.bat
echo :configurar >> menu.bat
echo notepad .env >> menu.bat
echo goto menu >> menu.bat
echo. >> menu.bat
echo :estado >> menu.bat
echo call venv\Scripts\activate.bat >> menu.bat
echo python -c "from database.connection_hybrid import db_hybrid; print('Estado:', db_hybrid.get_sync_status())" >> menu.bat
echo pause >> menu.bat
echo goto menu >> menu.bat
echo. >> menu.bat
echo :actualizar >> menu.bat
echo git pull >> menu.bat
echo call venv\Scripts\activate.bat >> menu.bat
echo pip install -r requirements_simple.txt >> menu.bat
echo echo Sistema actualizado >> menu.bat
echo pause >> menu.bat
echo goto menu >> menu.bat
echo. >> menu.bat
echo :salir >> menu.bat
echo exit >> menu.bat

echo.
echo ============================================
echo     INSTALACION COMPLETADA
echo ============================================
echo.
echo El sistema Mi Chas-K ha sido instalado exitosamente.
echo.
echo CONFIGURACION AUTOMATICA APLICADA:
echo - Variables de entorno configuradas automaticamente
echo - Conexion a base de datos Render preconfigurada
echo - Sistema hibrido habilitado ^(funciona offline/online^)
echo.
echo PROXIMOS PASOS:
echo.
echo 1. El sistema ya esta LISTO PARA USAR
echo    ^(No necesitas configurar nada mas^)
echo.
echo 2. Ejecuta el sistema usando:
echo    - Doble clic en "menu.bat" ^(recomendado^)
echo    - O doble clic en "iniciar.bat" ^(directo^)
echo.
echo 3. El sistema se abrira en tu navegador en:
echo    http://localhost:8501
echo.
echo FUNCIONALIDADES:
echo - ✅ Funciona SIN internet ^(modo local^)
echo - ✅ Se sincroniza automaticamente cuando hay internet
echo - ✅ Conecta a base de datos en la nube automaticamente
echo - ✅ Punto de venta simplificado y rapido
echo - ✅ Gestion de inventario completa
echo - ✅ Dashboard de ventas en tiempo real
echo - ✅ Configuracion y mantenimiento facil
echo.

:: Abrir archivo de configuracion
notepad .env

echo.
echo Presiona cualquier tecla para continuar...
pause >nul

:: Preguntar si quiere iniciar ahora
set /p iniciar="¿Quieres iniciar el sistema ahora? (s/n): "
if /i "%iniciar%"=="s" (
    echo.
    echo [INFO] Iniciando Mi Chas-K...
    call iniciar.bat
)

echo.
echo ¡Gracias por usar Mi Chas-K!
pause
