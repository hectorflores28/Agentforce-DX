from fastmcp import FastMCP
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import json
import pymysql
from datetime import date
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Inicializar FastMCP
mcp = FastMCP("N8n-Typebot-Server")

# Forzar la creación de la app FastAPI interna definiendo una herramienta dummy
@mcp.tool()
def _init_mcp():
    pass

# Configurar middleware de FastAPI si existe
if hasattr(mcp, "_app") and mcp._app:
    mcp._app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @mcp._app.post("/sse")
    async def sse_post_handler(request: Request):
        return await mcp._app.handlers.get("post_messages")(request)

def get_db_connection():
    """Retorna una conexión a la base de datos MySQL local"""
    return pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "db_user"),
        password=os.getenv("DB_PASSWORD", "db_password_here"),
        database=os.getenv("DB_NAME", "messaging_session"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

@mcp.tool()
async def analyze_customer_intent(message_text: str, session_id: str = None) -> str:
    """
    Analiza el texto de un cliente usando el LLM local (Ollama) para extraer intenciones
    e información clave (Nombre, Teléfono, Motivo, Score de interés y si amerita escalado).
    """
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
    prompt = f"""
    Analiza el siguiente mensaje de un cliente de hotel/resort:
    "{message_text}"

    Extrae la siguiente información estructurada en formato JSON estricto:
    - nombre: Nombre del cliente (si lo menciona, o null)
    - telefono: Teléfono (si lo menciona, o null)
    - motivo: Motivo del mensaje (ej. Cotización, Queja, Reserva, Mascotas, etc.)
    - es_cotizacion_o_reserva: true o false (si es una intención de compra o reserva de estancia)
    - requiere_escalacion: true o false (si requiere que un humano lo atienda de inmediato)
    - propiedad: Nombre de la propiedad que le interesa (ej. Casa xxx, xxx Vallarta, etc., o null)

    Responde SOLAMENTE el JSON válido, sin explicaciones ni markdown.
    """
    
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{ollama_host}/api/generate",
                json={
                    "model": "llama3", # O el modelo configurado en tu Ollama local
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=30.0
            )
            res.raise_for_status()
            response_json = res.json()
            return response_json.get("response", "{}")
    except Exception as e:
        return json.dumps({
            "error": f"Error al consultar Ollama: {str(e)}",
            "nombre": None,
            "telefono": None,
            "motivo": "Error de inferencia",
            "es_cotizacion_o_reserva": False,
            "requiere_escalacion": True,
            "propiedad": None
        })

@mcp.tool()
def log_interaction_mysql(
    session_id: str,
    sender_type: str,
    sender_name: str,
    message_text: str,
    handled_by_bot: int = 1,
    escalated_to_human: int = 0
) -> str:
    """
    Registra el mensaje y actualiza/crea la sesión en la base de datos MySQL local para reportería a coste cero.
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 1. Asegurar que existe la sesión
            cursor.execute(
                """
                INSERT INTO sessions (session_id, session_date, handled_by_bot, escalated_to_human)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    updated_at = CURRENT_TIMESTAMP,
                    handled_by_bot = VALUES(handled_by_bot),
                    escalated_to_human = VALUES(escalated_to_human)
                """,
                (session_id, date.today(), handled_by_bot, escalated_to_human)
            )
            
            # 2. Insertar el mensaje
            cursor.execute(
                """
                INSERT INTO messages (session_id, sender_type, sender_name, message_text)
                VALUES (%s, %s, %s, %s)
                """,
                (session_id, sender_type.upper(), sender_name, message_text)
            )
            conn.commit()
            conn.close()
            return f"Exito: Registrada interacción para la sesión {session_id}."
    except Exception as e:
        return f"Error en BD MySQL: {str(e)}"

if __name__ == "__main__":
    import sys
    if "--sse" in sys.argv:
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", "8000"))
        print(f"🚀 Iniciando servidor MCP SSE en {host}:{port}")
        mcp.run(transport="sse", host=host, port=port)
    else:
        mcp.run(transport="stdio")
