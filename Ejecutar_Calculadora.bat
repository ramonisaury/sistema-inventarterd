@echo off
title Sistema de Calculo - Server
color 0b

:: Cambiar a la ruta de tu carpeta
cd /d "C:\Users\ingbe\Calculo precios sistema"

echo ===========================================
echo   INICIANDO SERVIDOR DE BASE DE DATOS
echo ===========================================

:: Iniciar Python en una ventana aparte pero minimizada
start /min cmd /c "python app.py"

:: Esperar a que el servidor Flask este listo
echo Esperando conexion con Python...
timeout /t 3 /nobreak > nul

:: Abrir el archivo HTML (Cambia 'index.html' por el nombre real de tu archivo)
echo Abriendo Interfaz en el navegador...
start "" "static/Calcular precio impresion.html"

echo.
echo [LISTO] El sistema esta corriendo. 
echo No cierres esta ventana si quieres seguir usando la DB.
echo.
pause