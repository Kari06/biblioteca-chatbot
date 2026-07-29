from flask import Flask, render_template, request, jsonify
import json
import unicodedata
import difflib
import os
import logging
from datetime import datetime

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "chatbot.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

UNANSWERED_PATH = os.path.join(BASE_DIR, "unanswered.json")
FEEDBACK_PATH = os.path.join(BASE_DIR, "feedback.json")
UMBRAL_CONFIANZA = 0.82  # Umbral mínimo de similitud para aceptar una coincidencia difusa


# ----------------------------
# UTILIDADES DE ARCHIVOS
# ----------------------------
def cargar_json(ruta, valor_default):
    """Carga un JSON de forma segura. Si no existe o está corrupto, usa un valor por defecto."""
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning(f"No se encontró el archivo {ruta}, usando valor por defecto.")
        return valor_default
    except json.JSONDecodeError as e:
        logging.error(f"Error al leer JSON en {ruta}: {e}")
        return valor_default


def guardar_json(ruta, datos):
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"No se pudo guardar el archivo {ruta}: {e}")


# ----------------------------
# CARGAR BASE DE CONOCIMIENTO Y SUGERENCIAS
# ----------------------------
knowledge = cargar_json(os.path.join(BASE_DIR, "knowledge.json"), [])
suggestions = cargar_json(os.path.join(BASE_DIR, "suggestions.json"), [])


# ----------------------------
# LIMPIEZA DE TEXTO
# ----------------------------
def limpiar_texto(texto):
    texto = texto.lower().strip()
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto


# ----------------------------
# MOTOR DE COINCIDENCIA (exacta + difusa)
# ----------------------------
def buscar_respuesta(mensaje_limpio):
    """
    1. Coincidencia exacta: la keyword aparece como substring del mensaje.
    2. Coincidencia difusa (difflib): tolera errores de tipeo comparando
       palabra por palabra contra cada keyword.
    Devuelve (respuesta, score, intent_id) o (None, score, None) si no hay match.
    """
    # 1. Coincidencia exacta por substring
    for intent in knowledge:
        for keyword in intent["keywords"]:
            if limpiar_texto(keyword) in mensaje_limpio:
                return intent["response"], 1.0, intent.get("id")

    # 2. Coincidencia difusa palabra por palabra
    palabras_mensaje = mensaje_limpio.split()
    mejor_intent = None
    mejor_score = 0.0

    for intent in knowledge:
        for keyword in intent["keywords"]:
            keyword_limpio = limpiar_texto(keyword)
            for palabra in palabras_mensaje:
                score = difflib.SequenceMatcher(None, palabra, keyword_limpio).ratio()
                if score > mejor_score:
                    mejor_score = score
                    mejor_intent = intent

    if mejor_intent and mejor_score >= UMBRAL_CONFIANZA:
        return mejor_intent["response"], mejor_score, mejor_intent.get("id")

    return None, mejor_score, None


# ----------------------------
# RUTA PRINCIPAL
# ----------------------------
@app.route("/")
def home():
    return render_template("index.html", suggestions=suggestions)


# ----------------------------
# RUTA DEL CHAT
# ----------------------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)

    if not data or "message" not in data or not str(data["message"]).strip():
        return jsonify({"response": "Por favor escribe una pregunta para poder ayudarte 🙂"}), 400

    mensaje_original = str(data["message"]).strip()[:500]  # límite razonable de longitud
    mensaje_limpio = limpiar_texto(mensaje_original)

    respuesta, score, intent_id = buscar_respuesta(mensaje_limpio)
    logging.info(f"Consulta: '{mensaje_original}' | Score: {score:.2f} | Intent: {intent_id}")

    if respuesta:
        return jsonify({"response": respuesta, "matched": True})

    # Registrar preguntas sin respuesta para revisar y ampliar la base de conocimiento
    entradas = cargar_json(UNANSWERED_PATH, [])
    entradas.append({
        "mensaje": mensaje_original,
        "mensaje_normalizado": mensaje_limpio,
        "fecha": datetime.now().isoformat()
    })
    guardar_json(UNANSWERED_PATH, entradas)

    return jsonify({
        "response": "No encontré información exacta sobre eso 🤔 Pero puedes escribirnos a biblioteca@castrocarazo.ac.cr o recordar que la Biblioteca Virtual es tu aliada estratégica para el éxito académico 📚✨",
        "matched": False
    })


# ----------------------------
# RUTA DE FEEDBACK (👍 / 👎)
# ----------------------------
@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json(silent=True) or {}

    entradas = cargar_json(FEEDBACK_PATH, [])
    entradas.append({
        "mensaje": data.get("message", ""),
        "respuesta": data.get("response", ""),
        "util": data.get("useful"),
        "fecha": datetime.now().isoformat()
    })
    guardar_json(FEEDBACK_PATH, entradas)

    return jsonify({"status": "ok"})


# ----------------------------
# RUTA DE SALUD (para monitoreo)
# ----------------------------
@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "knowledge_entries": len(knowledge),
        "suggestions": len(suggestions)
    })


# ----------------------------
# EJECUTAR APP
# ----------------------------
if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode)
