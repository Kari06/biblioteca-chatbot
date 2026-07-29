# Asistente Biblioteca Virtual — Universidad Castro Carazo

Chatbot institucional basado en reglas (intents + keywords) con respaldo de
coincidencia difusa para tolerar errores de tipeo. Construido con Flask +
HTML/CSS/JS puro (sin frameworks pesados de frontend).

## Estructura del proyecto

```
biblioteca_chatbot/
├── app.py                  # Backend Flask
├── knowledge.json          # Base de conocimiento (intents, keywords, respuestas)
├── suggestions.json        # Botones de sugerencia en pantalla de inicio
├── requirements.txt
├── templates/
│   └── index.html          # Interfaz de chat
├── static/                 # (reservado para futuros assets: logo, imágenes)
├── logs/                   # Se crea automáticamente al ejecutar (no subir a git)
├── unanswered.json         # Preguntas sin respuesta, generado en runtime
└── feedback.json           # Feedback 👍/👎 de usuarios, generado en runtime
```

## Cómo ejecutarlo

```bash
pip install -r requirements.txt
python app.py
```

Por defecto corre en modo producción (`debug=False`). Para desarrollo local:

```bash
FLASK_DEBUG=true python app.py
```

## Qué cambió respecto a la versión original

1. **Contenido**: se eliminó una entrada en `knowledge.json` que calificaba a
   una bibliotecóloga por apariencia física ("la más guapa es la de
   colochitos"). Se reemplazó por una descripción profesional del equipo.
   Este tipo de contenido no debería estar en un asistente institucional,
   independientemente de la intención con que se escribió originalmente.
2. **Base de conocimiento ampliada**: de 7 a 17 intents, incluyendo bases de
   datos (O'Reilly, AlphaCloud, Tirant Prime), repositorio de tesis, préstamos
   físicos, certificados de capacitación, contacto humano/escalación, saludo
   y despedida.
3. **Coincidencia difusa**: además del match exacto por substring, ahora se
   compara cada palabra del mensaje contra las keywords con `difflib`
   (stdlib, sin dependencias externas) para tolerar errores de tipeo
   (ej. "aceso" → "acceso").
4. **Manejo de errores**: carga segura de JSON (no truena si falta un archivo
   o está corrupto), validación del body en `/chat`, límite de longitud del
   mensaje.
5. **Logging**: cada consulta se registra en `logs/chatbot.log` con el score
   de coincidencia y el intent detectado — útil para depurar por qué un
   mensaje no dio la respuesta esperada.
6. **Aprendizaje continuo**: las preguntas sin respuesta se guardan en
   `unanswered.json`. Revisar este archivo periódicamente es la forma más
   directa de detectar huecos en la base de conocimiento y decidir qué
   nuevos intents agregar.
7. **Feedback de usuarios**: botones 👍/👎 bajo cada respuesta del bot,
   guardados en `feedback.json` vía el endpoint `/feedback`.
8. **Nuevo endpoint `/health`**: útil si en algún momento se despliega detrás
   de un balanceador o se quiere monitorear que el servicio esté activo.
9. **Seguridad**: `debug=True` ya no está hardcodeado; se controla con la
   variable de entorno `FLASK_DEBUG` (nunca debe ir en `true` en producción).
10. **Frontend**: diseño renovado (responsive, meta viewport para móviles),
    indicador de "escribiendo" animado en vez de texto estático, foco
    automático en el input, botón de enviar deshabilitado mientras se espera
   respuesta, mejoras de accesibilidad (`aria-label`, `aria-live`).

## Cómo agregar una nueva pregunta/respuesta

Edita `knowledge.json` y agrega un objeto:

```json
{
    "id": "identificador_unico",
    "keywords": ["palabra1", "palabra2", "frase corta"],
    "response": "Texto de la respuesta."
}
```

No hace falta reiniciar nada más que el servidor Flask. Las keywords no
necesitan tildes (el sistema las normaliza automáticamente).

## Próximos pasos posibles (no implementados aún)

- **Panel de administración** simple para editar `knowledge.json` desde el
  navegador en vez de tocar el JSON a mano.
- **Similitud semántica real** (embeddings) si en algún momento se quiere ir
  más allá de keywords — por ejemplo con la API de Anthropic o un modelo de
  sentence-embeddings local, usando `unanswered.json` como insumo para
  entrenar/ajustar.
- **Panel de métricas** a partir de `feedback.json` y `unanswered.json` para
  ver qué tan bien está respondiendo el bot y detectar áreas débiles —tiene
  bastante sinergia con un enfoque de gestión de datos/gobierno de datos
  aplicado al servicio de biblioteca."}
]
