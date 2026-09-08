# 🎨 MANUAL DE IDENTIDAD VISUAL Y DISEÑO DE INTERFACES (UI/UX)
## SISTEMA DE PRODUCCIÓN INTEGRAL (SPI)

> **Propósito del Documento:**  
> Este documento establece los estándares de diseño, paleta cromática, tipografías, componentes y reglas de orden visual que deben respetarse rigurosamente en todos los desarrollos del ecosistema SPI (Terminales Python de planta, Módulos Android de granja, Vistas de gestión en AppSheet y Reportes Web).

---

## 1. FILOSOFÍA Y FUNDAMENTOS DE DISEÑO INDUSTRIAL

El software del SPI opera en entornos exigentes: frigoríficos, salas de desposte húmedas o frías, fábricas de chacinados con polvillo de harinas/especias, galpones de granja con luz solar directa y locales comerciales de atención rápida.

### 📌 Principios Rectores:
1. **Legibilidad Inmediata a Distancia (Regla de los 2 Metros):** Los datos clave (peso de balanza, código de lote, corte seleccionado) deben leerse claramente a 2 metros de distancia de la pantalla táctil.
2. **Touch-First & Glove-Friendly (Diseñado para Dedos y Guantes):** Todos los botones operativos deben tener un tamaño mínimo de **54px a 64px** de alto, con separación suficiente para evitar pulsaciones erróneas de operarios con guantes o dedos húmedos.
3. **Dark Mode Industrial Obligatorio por Defecto:**
   - Reduce la fatiga visual del operario en turnos continuos.
   - Brinda contraste superior (WCAG AAA) bajo luces fluorescentes o LED de planta.
   - Oculta mejor manchas y reflejos en pantallas táctiles industriales.
4. **Retroalimentación Inmediata (Visual y Sonora):** Cada acción física (pesaje capturado, etiqueta impresa, registro guardado) debe producir un cambio de estado visual evidente (flash de confirmación, cambio de color de borde) y/o un sonido de confirmación.
5. **Tolerancia a Errores y Confirmación Crítica:** Acciones irreversibles (anular tropa, decomiso de res, cancelar bachada) requieren doble confirmación con advertencia visual explícita en color ámbar/rojo.

---

## 2. PALETA CROMÁTICA OFICIAL (DESIGN TOKENS)

La paleta se basa en una estructura **Dark Slate & Deep Indigo**, complementada con semáforos cromáticos de alto contraste para estados industriales.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PALETA DE COLORES SPI                            │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│  DEEP CANVAS    │  SURFACE PANEL  │ BRAND PRIMARY   │  SUCCESS / PESADA OK  │
│    #0B0F19      │    #0F172A      │    #6366F1      │       #10B981         │
├─────────────────┼─────────────────┼─────────────────┼───────────────────────┤
│ CARD ELEVATED   │ BORDER MUTED    │ BRAND GRADIENT  │  WARNING / SOBRANTE   │
│    #171F36      │    #334155      │ #6366F1 → #8B5CF6│       #F59E0B         │
├─────────────────┼─────────────────┼─────────────────┼───────────────────────┤
│ TEXT PRIMARY    │ TEXT SECONDARY  │ BALANZA ACCENT  │  ERROR / DECOMISO     │
│    #F8FAFC      │    #94A3B8      │    #38BDF8      │       #EF4444         │
└─────────────────┴─────────────────┴─────────────────┴───────────────────────┘
```

### 2.1. Fondos y Superficies (Backgrounds & Surfaces)
| Nombre del Token | Código HEX | Uso Principal |
|---|---|---|
| `--bg-canvas` | `#0B0F19` | Fondo principal de la ventana y aplicaciones. |
| `--bg-surface` | `#0F172A` | Paneles laterales, contenedores de sección, modales. |
| `--bg-card` | `#171F36` | Tarjetas interactivas, grupos de inputs, tarjetas de resumen. |
| `--bg-card-hover` | `#1E293B` | Estado hover de tarjetas y filas de tablas. |
| `--bg-input` | `#060911` | Fondo de campos de texto, inputs y displays numéricos. |
| `--border-subtle` | `#1E293B` | Separadores secundarios y bordes pasivos. |
| `--border-default` | `#334155` | Bordes estándar de botones secundarios, tarjetas e inputs. |
| `--border-focus` | `#6366F1` | Borde de elementos activos o en foco. |

---

### 2.2. Colores Primarios y de Identidad (Brand Identity)
| Nombre del Token | Código HEX | Uso Principal |
|---|---|---|
| `--primary` | `#6366F1` | Botones de acción principal, pestañas activas, elementos clave. |
| `--primary-hover` | `#4F46E5` | Estado hover / presionado de botones primarios. |
| `--primary-glow` | `#6366F14D` | Sombras y resplandores luminosos (`box-shadow`). |
| `--accent-gradient` | `linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)` | Encabezados de portal, títulos principales, badges destacados. |

---

### 2.3. Semáforo Industrial y Estados Semánticos
| Estado | Color HEX | Badge Background | Badge Border | Significado Operativo |
|---|---|---|---|---|
| **Éxito / Conforme** | `#10B981` | `#10B98126` | `#10B9814D` | Peso capturado estable, sincronizado online, rendimiento dentro de tolerancia, stock correcto. |
| **Advertencia** | `#F59E0B` | `#F59E0B26` | `#F59E0B4D` | Peso inestable / en movimiento, cola de sincronización pendiente, merma fuera de rango, stock sobrante. |
| **Peligro / Error** | `#EF4444` | `#EF444426` | `#EF44444D` | Decomiso veterinario, desconexión de balanza, stock faltante crítico, error de comunicación. |
| **Balanza / Métricas** | `#38BDF8` | `#38BDF826` | `#38BDF84D` | Lectura de peso en vivo, kilogramos netos, valores informativos de báscula. |
| **Inactivo / Neutral** | `#64748B` | `#64748B26` | `#64748B4D` | Botones deshabilitados, metadatos, timestamps pasivos. |

---

### 2.4. Jerarquía de Textos y Contraste
| Nivel | Código HEX | Opacidad / Peso | Uso |
|---|---|---|---|
| **Texto Primario** | `#F8FAFC` | 100% / Regular a Bold | Títulos, valores de pesaje, nombres de artículos. |
| **Texto Secundario** | `#94A3B8` | 80% / Medium | Subtítulos, labels de campos, unidades (`kg`, `un`). |
| **Texto Terciario** | `#64748B` | 60% / Regular | Timestamps, IDs de auditoría, números de versión. |
| **Texto Invertido** | `#0B0F19` | 100% / Bold | Texto sobre fondos brillantes (ej. badges de advertencia). |

---

## 3. SISTEMA TIPOGRÁFICO Y JERARQUÍA ESCALAR

### 3.1. Familias Tipográficas (Font Stacks)
1. **Tipografía de Interfaz General:**  
   `"Outfit", "Segoe UI", "Roboto", -apple-system, sans-serif`  
   *Uso:* Títulos, botones, formularios, etiquetas y navegación.
2. **Tipografía Numérica y de Datos (Monospace):**  
   `"JetBrains Mono", "Roboto Mono", "Consolas", monospace`  
   *Uso:* Display gigante de balanzas, códigos de lote (`LOT-2026-09-001`), códigos de barras, pesos numéricos en tablas. Evita saltos de ancho al cambiar los dígitos.

---

### 3.2. Escala Tipográfica para Terminales Industriales y Desktop
| Nivel | Tamaño | Peso (Weight) | Transformación | Aplicación |
|---|---|---|---|---|
| **Display Balanza** | `56px - 72px` | 800 (Extrabold) Monospace | Normal | Indicador gigante de peso en tiempo real. |
| **H1 - Pantalla Principal** | `26px - 30px` | 700 (Bold) | Normal | Título del módulo (`FAENA - PESAJE AL GANCHO`). |
| **H2 - Sección / Panel** | `20px - 22px` | 600 (Semibold) | Normal | Títulos de tarjetas (`Resumen de la Tropa`). |
| **H3 - Subsección / Modal**| `16px - 18px` | 600 (Semibold) | Normal | Cabeceras de formularios o modales. |
| **Body (Texto Estándar)** | `14px - 15px` | 400 - 500 (Medium) | Normal | Filas de tablas, textos descriptivos. |
| **Form Labels** | `12px - 13px` | 600 (Semibold) | **MAYÚSCULAS** (`letter-spacing: +0.5px`) | Etiquetas sobre inputs (`CORTE MADRE`, `DT-E SENASA`). |
| **Badges / Micro-tags** | `10px - 11px` | 700 (Bold) | **MAYÚSCULAS** | Estados (`ESTABLE`, `PENDIENTE`, `IZQ`, `DER`). |

---

## 4. REGLAS DE ORDEN VISUAL Y ESTRUCTURA DE PANTALLA

Todas las pantallas operativas deben seguir una división tripartita estricta:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. HEADER OPERATIVO (Alto: 64px)                                           │
│ [LOGO SPI]  Módulo: DESPIECE FABRICA  │ Op: Juan Pérez  │ 🟢 ONLINE (COM3) │
├───────────────────────────────────────┬─────────────────────────────────────┤
│ 2. ÁREA DE TRABAJO IZQUIERDA (55%)    │ 3. ÁREA DE BÁSCULA Y RESUMEN (45%)  │
│                                       │                                     │
│  [ Seleccionar Corte / Receta ]       │  ┌───────────────────────────────┐  │
│  ┌───────────┐ ┌───────────┐          │  │ DISPLAY BÁSCULA (MONOSPACE)   │  │
│  │  PALETA   │ │   JAMÓN   │          │  │        84.550 kg             │  │
│  └───────────┘ └───────────┘          │  │  ● ESTABLE [BALANZA GANCHO]   │  │
│  ┌───────────┐ ┌───────────┐          │  └───────────────────────────────┘  │
│  │   CARRE   │ │  PECHITO  │          │                                     │
│  └───────────┘ └───────────┘          │  [ ⚖️ CAPTURAR PESO & IMPRIMIR ]   │
│                                       │                                     │
│  [ Inputs de Proceso / Lote ]         │  Últimas Capturas (Tabla resumida)  │
│                                       │  - Media Res Der: 42.30 kg (ZPL OK) │
│                                       │  - Media Res Izq: 42.25 kg (ZPL OK) │
├───────────────────────────────────────┴─────────────────────────────────────┤
│ 4. FOOTER DE ACCIONES GLOBALES (Alto: 70px)                                │
│ [ ❌ CANCELAR / VOLVER ]               [ 💾 FINALIZAR SESIÓN / TROPA (F10) ]│
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.1. Reglas de Composición Visual:
1. **Espaciado en Múltiplos de 8px:**  
   Márgenes y paddings estándar: `8px`, `16px`, `24px`, `32px`. No usar espaciados arbitrarios (como 7px o 13px).
2. **Jerarquía Visual de Izquierda a Derecha:**  
   - **Izquierda:** Selección de origen / entrada de datos / filtros.
   - **Centro / Derecha:** Acción física (pesada) y resultados inmediatos.
   - **Abajo:** Confirmación global del ciclo de trabajo.
3. **Alineación de Datos:**
   - Textos descriptivos: Alineados a la **Izquierda**.
   - Números, pesos, importes y fechas: Alineados a la **Derecha** o **Centrados**.
   - Códigos y Badges: **Centrados**.
4. **Tarjetas con Profundidad y Bordes Definidos:**  
   Todo contenedor debe poseer un borde de `1px solid #334155` y radio de curvatura (`border-radius: 14px` o `16px`).

---

## 5. ESPECIFICACIÓN DE COMPONENTES DE INTERFAZ

### 5.1. El Display de Balanza Industrial (Scale Card)
Es el componente central de las terminales de frigorífico y fábrica.

- **Fondo:** `#050811` (Negro profundo).
- **Borde Dinámico según Estado:**
  - *Estable:* `2px solid #10B981` con resplandor verde sutil.
  - *Inestable / Movimiento:* `2px dashed #F59E0B` con animación intermitente.
  - *Desconectada / Error:* `2px solid #EF4444`.
- **Tipografía del Número:** `JetBrains Mono` o `Roboto Mono`, tamaño `60px` a `72px`, peso `800`, color `#FFFFFF`.
- **Unidad de Medida:** `kg` en color `#38BDF8`, tamaño `24px`, pegado al valor.
- **Indicador de Estado:** Píldora en la esquina superior derecha:
  - `● ESTABLE` (Verde `#10B981`)
  - `◌ LEYENDO...` (Ámbar `#F59E0B`)
  - `✕ SIN SEÑAL` (Rojo `#EF4444`)

---

### 5.2. Botones Operativos (Action Buttons)

```
┌─────────────────────────────────────────────────────────────┐
│ [BOTÓN PRIMARIO / PESAR]         alto: 58px | radio: 12px   │
│ Background: #6366F1             Hover: #4F46E5              │
│ Texto: 16px Bold #FFFFFF        Sombra: 0 4px 15px #6366F14D│
├─────────────────────────────────────────────────────────────┤
│ [BOTÓN DE CONFIRMACIÓN / ÉXITO]  alto: 58px | radio: 12px   │
│ Background: #10B981             Hover: #059669              │
├─────────────────────────────────────────────────────────────┤
│ [BOTÓN SECUNDARIO / CANCELAR]    alto: 48px | radio: 10px   │
│ Background: #1E293B             Border: 1.5px solid #334155 │
│ Texto: 14px Semibold #F8FAFC    Hover: #334155              │
├─────────────────────────────────────────────────────────────┤
│ [BOTÓN DECOMISO / PELIGRO]       alto: 48px | radio: 10px   │
│ Background: #EF444426           Border: 1.5px solid #EF4444 │
│ Texto: 14px Bold #F87171        Hover: #EF44444D            │
└─────────────────────────────────────────────────────────────┘
```

- **Comportamiento Táctil:** Al ser presionado (`:active`), el botón debe escalar levemente a `transform: scale(0.98)` para brindar sensación física de clic.
- **Deshabilitado (`disabled`):** Opacidad al `40%`, cursor `not-allowed`, sin eventos táctiles.

---

### 5.3. Campos de Entrada (Input Fields & Selects)
- **Fondo:** `#080C16`.
- **Borde Normal:** `1.5px solid #334155`, radio `10px`.
- **Borde en Foco:** `1.5px solid #6366F1`, resplandor `box-shadow: 0 0 10px #6366F133`.
- **Etiqueta (Label):** Ubicada **siempre arriba del campo** (nunca depender únicamente del placeholder), tamaño `12px`, mayúsculas, color `#94A3B8`.
- **Padding Interno:** `12px 14px` (suficientemente alto para tocar con el dedo).

---

### 5.4. Teclado Numérico en Pantalla (Numpad Táctil)
Para terminales sin teclado físico (ej. ingreso de PIN de operario, tara manual o cantidad de ristras):
- Botones de dígitos (0 al 9): Círculos o cuadrados redondeados de `64px x 64px`.
- Fondo: `#FFFFFF0A`, Borde: `1px solid #FFFFFF14`.
- Texto: `24px Bold #FFFFFF`.
- Botón de Borrar (⌫): Color ámbar `#F59E0B`.
- Botón de Enter (✔): Color verde `#10B981`.

---

### 5.5. Tablas de Auditoría y Listados de Producción
- **Header:** Fondo `#0F172A`, texto `#94A3B8`, mayúsculas `11px`, `letter-spacing: 0.5px`.
- **Filas:** Altura mínima `44px`, separadas por línea `#FFFFFF0D`. Hover en `#1E293B66`.
- **Celda de Lote:** Formato badge con fondo oscuro `#0B0F19` y texto monoespaciado `#38BDF8`.
- **Columna de Acciones:** Botones compactos con iconos claros (🗑️ Eliminar en rojo, 🖨️ Re-imprimir en índigo).

---

## 6. FORMATOS DE DATOS Y ESTÁNDARES DE VISUALIZACIÓN

Para asegurar uniformidad en reportes, tablas, terminales y etiquetas:

| Tipo de Dato | Formato Estándar | Ejemplo Visual |
|---|---|---|
| **Pesos / Balanza** | `#,##0.00 kg` (o 3 decimales si es alta precisión) | `84.50 kg` / `1,250.75 kg` |
| **Porcentajes / Rendimiento** | `0.0 %` (1 decimal) | `78.4 %` / `2.3 %` |
| **Fecha Corta** | `DD/MM/AAAA` | `02/09/2026` |
| **Fecha y Hora Operativa**| `DD/MM/AAAA HH:mm:ss` | `02/09/2026 09:45:12` |
| **Código de Tropa** | `TRP-YYYY-XXXXX` | `TRP-2026-00412` |
| **Código de Lote Madre** | `LOT-YYYY-MM-DD-CORTE` | `LOT-2026-09-02-CARRE` |
| **Código de Media Res** | `MR-[LADO]-[ID_TROPA]-[SECUENCIA]` | `MR-DER-00412-01` |
| **Código de Bachada** | `BACH-[RECETA]-[FECHA]-[SEC]` | `BACH-00049-260902-01` |
| **Moneda / Precios** | `\$ #,##0.00` | `\$ 4,850.00` |

---

## 7. ADAPTACIÓN SEGÚN LA PLATAFORMA

### 7.1. Terminales de Planta Python (CustomTkinter / Desktop)
- **Modo:** Pantalla Completa (Kiosk Mode) o ventana fija de `1280x800` / `1920x1080`.
- **Theme:** `AppearanceMode: "Dark"`, `ColorTheme: "blue"`.
- **Optimización:** Fuentes cargadas desde assets locales (sin dependencia de conexión a internet para renderizar fuentes web).

### 7.2. Módulos Android (Granja / Auditoría Móvil)
- **Tema:** Material You / Material 3 Dark Theme con los tokens de color SPI.
- **Iconografía:** Google Material Symbols (Rounded).
- **Entrada Rápida:** Soporte para autofoco en lectores de código de barras por cámara o láser integrado.

### 7.3. Aplicaciones AppSheet (Gestión y Control)
- **Branding Color:** Primary `#6366F1`.
- **Format Rules:**
  - *Estado OK / Conforme:* Icono verde `check_circle` + texto `#10B981`.
  - *Estado Pendiente / Alerta:* Icono naranja `warning` + texto `#F59E0B`.
  - *Decomiso / Baja:* Icono rojo `cancel` + texto `#EF4444`.
- **Vistas:** Vistas tipo *Deck* y *Table* con imágenes de cortes optimizadas y textos truncados a 2 líneas para mantener uniformidad.

### 7.4. Etiquetas Industriales Zebra (ZPL-II)
- **Sustrato:** Fondo blanco con impresión térmica negra 100% (monocromo).
- **Tipografía ZPL:**
  - Título / Producto: Fuente Escalable `^A0N,45,45` (Negrita visible).
  - Lote y Kilos: Fuente Grande `^A0N,55,55`.
  - Fecha y Operario: Fuente Estándar `^A0N,25,25`.
- **Códigos:**
  - Código de Barras: `Code-128` con altura mínima de `70 dots` para lectura rápida con pistola.
  - Código QR: Módulo tamaño `5` con corrección de error nivel `M`.

---

## 8. CHECKLIST DE CONTROL DE CALIDAD VISUAL (PARA DESARROLLADORES)

Antes de dar por finalizada una nueva pantalla o módulo, verificar:

- [ ] ¿La interfaz utiliza el fondo Dark estándar (`#0B0F19` / `#0F172A`)?
- [ ] ¿Todos los botones operativos tienen al menos **54px** de alto?
- [ ] ¿Los campos numéricos y lecturas de balanza utilizan tipografía monoespaciada?
- [ ] ¿Las unidades (`kg`, `un`) están claramente indicadas junto a cada número?
- [ ] ¿El indicador de estado de conexión (Online / Sync / Offline) es visible en el encabezado?
- [ ] ¿Los colores semánticos respetan la norma (Verde = OK, Ámbar = Alerta, Rojo = Decomiso/Peligro)?
- [ ] ¿El texto de los labels se encuentra ubicado en la parte superior de los inputs?
- [ ] ¿La pantalla es perfectamente operable mediante pantalla táctil sin ratón ni teclado físico?

---

*Este manual es de aplicación obligatoria para todas las interfaces del Sistema de Producción Integral (SPI).*
