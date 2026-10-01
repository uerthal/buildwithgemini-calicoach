# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
from typing import Any, Dict, List, Optional
import urllib.request
from zoneinfo import ZoneInfo

from app.a2ui_prompt import SYSTEM_INSTRUCTION
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors.agent_engine_sandbox_code_executor import (
    AgentEngineSandboxCodeExecutor,
)
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.cloud import firestore, storage
from google.genai import Client as GenAIClient
from google.genai import types

from app.a2ui_utils import a2ui_callback

MODEL = "gemini-2.5-flash"
IMAGE_MODEL = "gemini-3.1-flash-lite-image"
GCP_PROJECT_ID = "qwiklabs-gcp-03-c139e3a03bec"
STORAGE_BUCKET_NAME = "calicoach-assets-qwiklabs-gcp-03-c139e3a03bec"
AGENT_ENGINE_RESOURCE_NAME = (
    "projects/842523300026/locations/us-central1/reasoningEngines/608750660032135168"
)
SANDBOX_RESOURCE_NAME = (
    "projects/842523300026/locations/us-central1/reasoningEngines/608750660032135168/sandboxEnvironments/3722942523358838784"
)

# Hardcoded project ID as string to prevent project number resolution issues on Agent Platform
db = firestore.Client(project=GCP_PROJECT_ID)
storage_client = storage.Client(project=GCP_PROJECT_ID)
genai_image_client = GenAIClient(project=GCP_PROJECT_ID, location="global", vertexai=True)

# Agent Engine Sandbox Code Executor for safe Python execution
sandbox_code_executor = AgentEngineSandboxCodeExecutor(
    sandbox_resource_name=SANDBOX_RESOURCE_NAME,
    agent_engine_resource_name=AGENT_ENGINE_RESOURCE_NAME,
)




def list_calisthenics_skills(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Consulta el catálogo de habilidades y progresiones de calistenia disponibles en Firestore.

    Args:
        category: Opcional. Filtro por categoría (ej: 'Tirón (Pull)', 'Empuje estático (Isometría)', 'Equilibrio / Empuje vertical'). Si no se especifica, devuelve todas.

    Returns:
        Lista de habilidades con su nombre, nivel, prerrequisitos, músculos y técnica clave.
    """
    col_ref = db.collection("calisthenics_skills")
    docs = col_ref.stream()
    skills = []
    for doc in docs:
        data = doc.to_dict()
        if category and category.lower() not in data.get("category", "").lower():
            continue
        skills.append(data)
    skills.sort(key=lambda x: x.get("progression_order", 99))
    return skills


def get_skill_progression(skill_name_or_id: str) -> Dict[str, Any]:
    """Obtiene los detalles, prerrequisitos y técnica de una habilidad de calistenia específica.

    Args:
        skill_name_or_id: Nombre o identificador de la habilidad (ej: 'pull-up', 'muscle-up', 'handstand', 'front-lever', 'planche').

    Returns:
        Detalles completos de la habilidad o mensaje de error si no existe.
    """
    cleaned_id = skill_name_or_id.lower().strip().replace(" ", "-")
    doc_ref = db.collection("calisthenics_skills").document(cleaned_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()

    # Búsqueda por coincidencia en el nombre si el ID directo no coincide
    for d in db.collection("calisthenics_skills").stream():
        data = d.to_dict()
        if skill_name_or_id.lower() in data.get("name", "").lower() or skill_name_or_id.lower() in d.id:
            return data

    return {"error": f"No se encontró la habilidad '{skill_name_or_id}' en el catálogo."}


def log_workout_session(
    skill_or_exercise: str,
    sets: int,
    reps_or_seconds: str,
    rpe: int,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Registra una sesión o serie de entrenamiento de calistenia en el diario del atleta en Firestore.

    Args:
        skill_or_exercise: Nombre del ejercicio o habilidad realizada (ej: 'Dominadas', 'Tuck Front Lever', 'Pino').
        sets: Número de series completadas (ej: 4).
        reps_or_seconds: Repeticiones por serie o tiempo bajo tensión en segundos (ej: '8 reps' o '15 segs').
        rpe: Esfuerzo Percibido del 1 al 10 (RPE / Rate of Perceived Exertion).
        notes: Notas u observaciones adicionales sobre sensaciones, fatiga o agarre.

    Returns:
        Confirmación del registro guardado con su ID y fecha.
    """
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    record = {
        "exercise": skill_or_exercise,
        "sets": sets,
        "reps_or_seconds": reps_or_seconds,
        "rpe": rpe,
        "notes": notes or "",
        "created_at": timestamp,
    }
    doc_ref = db.collection("workout_logs").document()
    doc_ref.set(record)
    return {
        "status": "success",
        "log_id": doc_ref.id,
        "message": f"Sesión de {skill_or_exercise} registrada exitosamente.",
        "record": record,
    }


def get_recent_workouts(limit: int = 5) -> List[Dict[str, Any]]:
    """Recupera los últimos registros de entrenamiento de calistenia del atleta guardados en Firestore.

    Args:
        limit: Número máximo de registros a recuperar (por defecto 5).

    Returns:
        Lista de entrenamientos ordenados del más reciente al más antiguo.
    """
    col_ref = (
        db.collection("workout_logs")
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
    )
    docs = col_ref.stream()
    return [d.to_dict() for d in docs]


def assess_skill_readiness(
    target_skill: str,
    max_pullups: int = 0,
    straight_bar_dips: int = 0,
    dead_hang_seconds: int = 0,
    wall_handstand_seconds: int = 0,
    hollow_body_seconds: int = 0,
    tuck_lever_seconds: int = 0,
) -> Dict[str, Any]:
    """Evalúa de forma cuantitativa la preparación física del atleta para una habilidad objetivo y genera un roadmap personalizado.

    Args:
        target_skill: Nombre o ID de la habilidad deseada (ej: 'pull-up', 'muscle-up', 'handstand', 'front-lever', 'planche').
        max_pullups: Número máximo de dominadas estrictas consecutivas que puede hacer el usuario.
        straight_bar_dips: Número máximo de fondos en barra recta (o paralelas) consecutivos.
        dead_hang_seconds: Segundos que puede colgarse en barra fija en suspensión pasiva/activa.
        wall_handstand_seconds: Segundos que aguanta el pino contra la pared (pecho a pared).
        hollow_body_seconds: Segundos que aguanta en postura hollow body estricta en el suelo.
        tuck_lever_seconds: Segundos que aguanta en tuck front lever.

    Returns:
        Diccionario con porcentaje de preparación (readiness_score_pct), estado, requisitos cumplidos/faltantes y recomendación específica de entrenamiento.
    """
    skill_info = get_skill_progression(target_skill)
    if "error" in skill_info:
        return skill_info

    skill_id = skill_info.get("id", target_skill.lower())
    checks = []
    readiness = 0.0

    if "pull-up" in skill_id:
        c1 = {"metric": "Dead Hang", "required": "45s", "current": f"{dead_hang_seconds}s", "met": dead_hang_seconds >= 45}
        c2 = {"metric": "Hollow Body", "required": "30s", "current": f"{hollow_body_seconds}s", "met": hollow_body_seconds >= 30}
        checks = [c1, c2]
        score = (min(dead_hang_seconds / 45, 1.0) * 0.6) + (min(hollow_body_seconds / 30, 1.0) * 0.4)
        readiness = round(score * 100, 1)

    elif "muscle-up" in skill_id:
        c1 = {"metric": "Dominadas explosivas al pecho", "required": "10 reps", "current": f"{max_pullups} reps", "met": max_pullups >= 10}
        c2 = {"metric": "Fondos en barra recta", "required": "15 reps", "current": f"{straight_bar_dips} reps", "met": straight_bar_dips >= 15}
        checks = [c1, c2]
        pull_score = min(max_pullups / 10, 1.0) * 0.55
        dip_score = min(straight_bar_dips / 15, 1.0) * 0.45
        readiness = round((pull_score + dip_score) * 100, 1)

    elif "handstand" in skill_id:
        c1 = {"metric": "Pino contra pared (Chest-to-wall)", "required": "60s", "current": f"{wall_handstand_seconds}s", "met": wall_handstand_seconds >= 60}
        c2 = {"metric": "Hollow body hold", "required": "45s", "current": f"{hollow_body_seconds}s", "met": hollow_body_seconds >= 45}
        checks = [c1, c2]
        wall_score = min(wall_handstand_seconds / 60, 1.0) * 0.6
        core_score = min(hollow_body_seconds / 45, 1.0) * 0.4
        readiness = round((wall_score + core_score) * 100, 1)

    elif "front-lever" in skill_id:
        c1 = {"metric": "Dominadas estrictas", "required": "12 reps", "current": f"{max_pullups} reps", "met": max_pullups >= 12}
        c2 = {"metric": "Tuck Front Lever", "required": "20s", "current": f"{tuck_lever_seconds}s", "met": tuck_lever_seconds >= 20}
        checks = [c1, c2]
        pull_score = min(max_pullups / 12, 1.0) * 0.4
        tuck_score = min(tuck_lever_seconds / 20, 1.0) * 0.6
        readiness = round((pull_score + tuck_score) * 100, 1)

    else:
        # Para planche y otros movimientos avanzados
        c1 = {"metric": "Base de fuerza y control articular", "required": "Revisar progresión", "current": f"{straight_bar_dips} fondos / {max_pullups} dominadas", "met": straight_bar_dips >= 15}
        checks = [c1]
        readiness = min(round((straight_bar_dips / 15) * 100, 1), 100.0)

    is_ready = readiness >= 95.0
    status = "Listo para iniciar intentos técnicos" if is_ready else "Fase de acondicionamiento de fuerza base"

    missing = [c["metric"] for c in checks if not c["met"]]
    advice = (
        f"¡Enhorabuena! Cumples los prerrequisitos. Comienza practicando la técnica con bandas elásticas o repeticiones negativas."
        if is_ready
        else f"Concéntrate en mejorar: {', '.join(missing)}. La consistencia en estos ejercicios básicos protegerá tus articulaciones."
    )

    return {
        "skill": skill_info.get("name", target_skill),
        "readiness_score_pct": readiness,
        "status": status,
        "criteria_breakdown": checks,
        "focus_advice": advice,
    }


EXERCISES_API_URL = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"


def search_external_exercises(
    query: str,
    bodyweight_only: bool = True,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Consulta la base de datos pública de ejercicios abiertos (Free Exercise DB de public-apis) para obtener variaciones y detalles anatómicos.

    Args:
        query: Término de búsqueda en inglés (ej: 'pull-up', 'push-up', 'dip', 'plank', 'squat', 'chin-up').
        bodyweight_only: Si es True, filtra únicamente ejercicios con peso corporal sin equipamiento pesado. Por defecto True.
        limit: Cantidad máxima de resultados a retornar (por defecto 5).

    Returns:
        Lista de ejercicios con nombre, nivel de dificultad, músculos primarios y secundarios, e instrucciones paso a paso.
    """
    try:
        req = urllib.request.Request(
            EXERCISES_API_URL,
            headers={"User-Agent": "CaliCoach-App/1.0", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            all_exercises = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        return [{"error": f"No se pudo consultar el servicio público de ejercicios: {str(e)}"}]

    clean_q = query.lower().strip()
    results = []

    for item in all_exercises:
        name = item.get("name", "").lower()
        equipment = str(item.get("equipment") or "").lower()
        if bodyweight_only and equipment not in ("body only", "none", "other"):
            continue

        if clean_q in name or any(clean_q in m.lower() for m in item.get("primaryMuscles", [])):
            raw_images = item.get("images", [])
            image_urls = [
                f"https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/{img_path}"
                for img_path in raw_images
            ]
            results.append({
                "name": item.get("name"),
                "level": item.get("level"),
                "equipment": item.get("equipment"),
                "primary_muscles": item.get("primaryMuscles", []),
                "secondary_muscles": item.get("secondaryMuscles", []),
                "instructions": item.get("instructions", [])[:4],
                "demo_images": image_urls,
                "primary_demo_image_url": image_urls[0] if image_urls else None,
            })
            if len(results) >= limit:
                break

    return results


async def generate_exercise_visual(
    exercise_name: str,
    tool_context: ToolContext,
) -> Dict[str, Any]:
    """Genera una ilustración anatómica de la técnica y alineación de un ejercicio o postura de calistenia usando gemini-3.1-flash-lite-image.

    Guarda la imagen como artefacto de la sesión y la sube al bucket de Cloud Storage público para retornar su URL pública.

    Args:
        exercise_name: Nombre del ejercicio o postura de calistenia (ej: 'Hollow Body Hold', 'Handstand', 'Muscle-Up', 'Front Lever', 'Planche').

    Returns:
        Diccionario con el estado, nombre del ejercicio y la URL pública https de Cloud Storage.
    """
    prompt = (
        f"A clean, detailed anatomical illustration of the calisthenics exercise '{exercise_name}'. "
        "Show correct athletic form, body alignment, key active muscle groups highlighted, minimal modern fitness aesthetic, plain light background."
    )

    try:
        response = genai_image_client.models.generate_content(
            model=IMAGE_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            ),
        )
    except Exception as e:
        return {"error": f"Error al generar la imagen con el modelo {IMAGE_MODEL}: {str(e)}"}

    image_bytes = None
    mime_type = "image/jpeg"

    if response.candidates and response.candidates[0].content:
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                image_bytes = part.inline_data.data
                mime_type = part.inline_data.mime_type or "image/jpeg"
                break

    if not image_bytes:
        return {"error": "El modelo no retornó bytes de imagen válidos."}

    # Limpiar nombre para archivos y URLs
    clean_name = exercise_name.lower().strip().replace(" ", "_").replace("-", "_")
    ext = "jpg" if "jpeg" in mime_type else "png"
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{clean_name}_{timestamp}.{ext}"

    # 1. Guardar como artefacto en la sesión con tool_context.save_artifact
    artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    await tool_context.save_artifact(
        filename=filename,
        artifact=artifact_part,
        custom_metadata={"exercise": exercise_name, "model": IMAGE_MODEL},
    )

    # 2. Subir bytes directamente a Cloud Storage público
    bucket = storage_client.bucket(STORAGE_BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{STORAGE_BUCKET_NAME}/{filename}"

    return {
        "status": "success",
        "exercise": exercise_name,
        "filename": filename,
        "image_url": public_url,
        "message": f"Ilustración de {exercise_name} generada y subida exitosamente.",
    }


async def generate_memories_callback(callback_context: CallbackContext):
    """Callback para extraer hechos, marcas y preferencias del usuario hacia el Memory Bank."""
    if callback_context._invocation_context.memory_service is not None:
        await callback_context.add_session_to_memory()
    return None


instruction = SYSTEM_INSTRUCTION


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=sandbox_code_executor,
    instruction=instruction,
    tools=[
        PreloadMemoryTool(),
        list_calisthenics_skills,
        get_skill_progression,
        assess_skill_readiness,
        log_workout_session,
        get_recent_workouts,
        search_external_exercises,
        generate_exercise_visual,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
