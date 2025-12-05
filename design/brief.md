# Brief de Diseño — EntrenaProChile

Propósito
---------
Documento de arranque para el rediseño visual de EntrenaProChile. Aquí recogemos objetivos, restricciones, recursos disponibles y propuestas de paleta iniciales para validar antes de avanzar con mockups y componentes.

Objetivos del rediseño
----------------------
- Mejorar la legibilidad y el contraste (WCAG AA) en las pantallas públicas (Login, Forgot, Home).
- Unificar estilos mediante tokens (colores, tipografías, espaciados, radios).
- Crear componentes reutilizables (Button, Input, Card) que faciliten el mantenimiento.
- Mantener o mejorar la estética actual (tema oscuro) y ofrecer una ruta para tema claro si se requiere.

Público objetivo
-----------------
- Entrenadores y clientes de la plataforma — usuarios móviles y escritorio.
- Perfil: personas interesadas en rutinas y entrenamiento; esperan una UI profesional, clara y legible.

Activos disponibles
-------------------
- Logo y recursos gráficos: (añade aquí SVG/PNG si los tienes).
- Estado actual: tema oscuro ya implementado en CSS/Tailwind.

Preguntas clave (respóndelas cuando puedas)
-----------------------------------------
1. ¿Quieres mantener el tema oscuro como predeterminado? (Sí/No)
2. ¿Tienes preferencia por alguna tipografía (p. ej. Inter, Poppins) o podemos usar Google Fonts?
3. ¿Deseas que el rediseño incluya modo claro desde el primer entregable?
4. ¿Hay ejemplos de apps o referencias visuales que te gusten? (enlaces o capturas)
5. ¿Tienes colores corporativos que debemos respetar (hex/svgs)?

Restricciones técnicas
----------------------
- Proyecto usa Tailwind / Vite (ver `frontend/`). Podemos modificar `tailwind.config.js` o usar variables CSS.
- Evitar cambios que rompan la API o rutas existentes. Este trabajo es visual y frontend.

Entregables del primer hito (Discovery)
--------------------------------------
1. Este brief (archivo).
2. 2 paletas propuestas (aquí abajo).
3. Plan y siguientes pasos para auditoría UI.

Paleta propuesta A — Modern Dark (recomendada si quieres continuidad)
------------------------------------------------------------------
- Uso: tema oscuro, profesional, alto contraste.
- Primario: Cyan brillante — `#06B6D4` (uso en botones y acentos)
- Secundario: Azul profundo — `#0F172A` (fondo principal)
- Surface / Cards: `#0B1220` (cards), `#0E1624` (paneles alternos)
- Texto principal: `#E6EEF3` (texto principal)
- Texto secundario: `#9AA7B2` (subtexto / captions)
- Success / Action: `#10B981` (verde)
- Warning: `#F59E0B` (amarillo)
- Error: `#EF4444` (rojo)

Ejemplo de tokens (A)
- `--color-bg`: `#0F172A`
- `--color-surface`: `#0B1220`
- `--color-primary`: `#06B6D4`
- `--color-text`: `#E6EEF3`
- `--radius-md`: `12px`
- `--space-1`: `4px`; `--space-2`: `8px`; `--space-3`: `16px`; `--space-4`: `24px`

Paleta propuesta B — Energética (alternativa clara/contrastada)
----------------------------------------------------------------
- Uso: look más cálido y enérgico, válida si quieres destacar CTAs.
- Primario: Magenta / Rosado — `#FB7185`
- Secundario: Púrpura profundo — `#5B21B6`
- Surface / Cards: `#0B1220` (mantenemos cards oscuros) o en versión clara `#F7FAFC`
- Texto claro: `#0F172A`
- Texto en oscuro: `#111827`
- Action/Success: `#06D6A0`

Tokens básicos recomendados
---------------------------
- Tipografía: `Inter`, fallback `system-ui, -apple-system, 'Segoe UI', Roboto`.
- Tamaños base: `16px` raíz; headings: 28/22/18/16.
- Radii: `4px` (small), `8px` (default), `12px` (card)
- Elevación: sombras suaves para cards `0 6px 18px rgba(3,7,18,0.6)` (dark) y `0 8px 20px rgba(2,6,23,0.08)` (light)

Siguientes pasos (propuestos)
----------------------------
1. Confirma respuestas a las preguntas clave arriba (logo, tipografía, tema por defecto).
2. Yo realizo la auditoría visual de `Login`, `Forgot` y `Home` y propongo ajustes puntuales (1–2 horas).
3. Tras tu OK, defino tokens en `tailwind.config.js` y empiezo mockups de `Login` y `Forgot`.

Notas finales
-------------
Si quieres que cree assets Figma, puedo generar PNG/SVG con alta fidelidad y añadirlos al repositorio en `design/`.

---
Archivo generado automáticamente por el proceso de diseño inicial.
