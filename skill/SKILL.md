---
name: diseno-muros-contencion
description: Diseñar, revisar, predimensionar y documentar muros de contención en voladizo de concreto reforzado sobre zapata superficial, incluidas presiones de tierra, estabilidad externa, diseño estructural, drenaje y memoria de cálculo. Usar cuando el usuario solicite un muro nuevo, la comprobación de uno existente o la revisión de cálculos; no aplicar automáticamente a muros anclados, pantallas, suelo reforzado, gaviones o estabilidad global de laderas.
---

# Diseño de muros de contención

## Alcance y criterio profesional

Trabajar por metro lineal de muro y distinguir claramente entre predimensionamiento, verificación con información parcial y diseño sustentado en estudio geotécnico y norma definida.

No declarar que un muro es seguro ni emitir un diseño definitivo si faltan parámetros geotécnicos, geometría, acciones o norma aplicable. El diseño requiere revisión y firma de profesionales responsables. La estabilidad global, asentamientos, capacidad portante y parámetros del terreno deben estar respaldados por geotecnia; no sustituir ese análisis con la verificación de la sección del muro.

## Flujo de trabajo

1. Clasificar la solicitud y confirmar que se trata de un muro en voladizo de concreto reforzado sobre cimentación superficial. Si es otro sistema, delimitar qué partes de este flujo son aprovechables y solicitar el método o norma correspondiente.
2. Leer [references/datos-entrada.md](references/datos-entrada.md). Extraer primero la información disponible de archivos, planos, informes o mensajes. Pedir únicamente los datos faltantes que cambian el resultado.
3. Confirmar norma, combinaciones de carga, estados límite, sistema de unidades y edición. No mezclar factores de AASHTO, NSR, ACI, CCP u otra norma sin explicar la compatibilidad.
4. Leer [references/metodologia-calculo.md](references/metodologia-calculo.md) y desarrollar el cálculo con trazabilidad: hipótesis, ecuaciones, sustitución numérica, unidades, resultado, límite y estado CUMPLE/NO CUMPLE/NO VERIFICABLE.
5. Iterar la geometría si alguna verificación falla. Registrar qué dimensión o parámetro cambió y por qué; no ocultar iteraciones desfavorables relevantes.
6. Para memorias o informes, leer [references/estructura-entregable.md](references/estructura-entregable.md). Entregar tablas de entradas, cargas, combinaciones y verificaciones, más croquis cuando ayude a interpretar la geometría.

## Reglas de cálculo

- Mantener una sola convención de signos y un punto de toma de momentos explícito.
- Separar valores característicos o nominales de valores factorizados.
- Identificar cada carga: peso propio, relleno sobre talón o puntera, empuje, sobrecarga, agua, sismo, tráfico, barrera, impacto y otras acciones aplicables.
- Modelar el agua explícitamente. No suponer drenaje perfecto porque exista un dren dibujado; verificar el escenario drenado y, cuando corresponda, una condición desfavorable por obstrucción o nivel freático.
- Aplicar presión pasiva solo si la norma y la permanencia del suelo frente a la puntera permiten contar con ella. Mostrar también la verificación sin pasivo cuando sea prudente o exigido.
- No usar coeficientes de presión activa si el muro no puede deformarse lo suficiente; considerar presión en reposo u otro modelo compatible.
- No atribuir cohesión permanente al relleno sin justificación geotécnica. Cuando se use, mostrar sensibilidad con cohesión nula si su pérdida es plausible.
- Verificar, como mínimo, excentricidad o vuelco, deslizamiento, presiones de contacto/capacidad portante, asentamientos, estabilidad global, flexión, cortante, acero mínimo, fisuración/servicio, desarrollo/anclaje y drenaje. Marcar lo que depende de un especialista o de datos aún no disponibles.
- Para muros escalonados, alturas variables, geometría tridimensional o coronación con barrera, identificar secciones críticas; no extrapolar una sola sección sin sustento.
- Reportar unidades en cada tabla y evitar conversiones implícitas. Si la fuente está en unidades inglesas, convertir una sola vez y conservar los valores originales como control.

## Uso del ejemplo adjunto

El archivo [references/ejemplo-cdot/document.md](references/ejemplo-cdot/document.md) reproduce un ejemplo CDOT/AASHTO LRFD de muro en voladizo con barrera e impacto vehicular. Consultarlo únicamente para la secuencia de cálculo, identificación de cargas y verificaciones. Sus dimensiones, propiedades, factores y resultados no son valores por defecto. Algunas ecuaciones del texto extraído están dañadas; contrastarlas con las imágenes de página incluidas en esa misma carpeta antes de reutilizarlas.

## Resultado esperado

Cerrar cada trabajo con el nivel del resultado; norma y edición; sección adoptada; tabla consolidada de verificaciones; disposición del refuerzo según el nivel; condicionantes geotécnicos, hidráulicos, sísmicos y constructivos; datos pendientes y responsable de suministrarlos; y una conclusión limitada a la evidencia disponible.
