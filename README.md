# PadronesDash

**Análisis y unificación de padrones de cobertura médica**  
Desarrollado para el Ministerio de Salud de la Nación.
---

## ¿Qué hace esta aplicación?
PadronesDash es una pequeña aplicación web que permite:

1. **Unificar** uno o varios “padrones” de cobertura médica en un solo archivo.  
2. **Analizar** ese padrón para separar:
   - **EMP** (Entidades de Medicina Prepaga): extrae los afiliados con “Plan Parcial”.  
   - **OSN** (Obras Sociales Nacionales):  
     - Identifica “Multi-CUIT” (PAMI).  
     - Detecta “Pluriempleo” (afiliados que figuran en más de una OSN).  
   - **Duplicados** (mismas claves de persona) y **errores** de referencia (datos que no coinciden con los catálogos oficiales).  
3. **Descargar** un paquete ZIP con los resultados (archivos CSV) y un pequeño resumen de estadísticas.

Todo esto desde una interfaz web muy sencilla.

---

## ¿Para quién es?

- Equipos del Ministerio de Salud de la Nación y de la Superintendencia de Servicios de Salud  
- Inclusión en Receta digital
- Personal técnico y no técnico que necesite procesar rápidamente grandes listados de beneficiarios  

---

## Requisitos mínimos
- **Sistema operativo**: Windows 10+, macOS o Linux  
- **Python** 3.11 (recomendado)  
- **Memoria RAM**: idealmente 8 GB o más  
- Espacio en disco suficiente para los archivos de padrones (pueden ser varios GB)

---
