# Seed script for CaliCoach Firestore backend
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-c139e3a03bec"
db = firestore.Client(project=PROJECT_ID)

SKILLS_DATA = [
    {
        "id": "pull-up",
        "name": "Dominada Estricta (Pull-Up)",
        "level": "Principiante / Básico",
        "category": "Tirón (Pull)",
        "target_muscles": ["Dorsal ancho", "Bíceps", "Trapecio", "Core"],
        "prerequisites": ["Dead Hang (45s)", "Dominadas Australianas / Inverted Rows (3x10)"],
        "progression_order": 1,
        "key_cues": "Retracción y depresión escapular antes de iniciar el tirón, barbilla sobre la barra, cuerpo en hollow body."
    },
    {
        "id": "handstand",
        "name": "Pino / Handstand Libre",
        "level": "Intermedio",
        "category": "Equilibrio / Empuje vertical",
        "target_muscles": ["Deltoides", "Trapecio superior", "Serrato anterior", "Core", "Flexores muñeca"],
        "prerequisites": ["Pino contra pared (Chest-to-wall 60s)", "Hollow body hold (45s)", "Pike push-ups (3x8)"],
        "progression_order": 2,
        "key_cues": "Bloqueo articular de codos, empuje activo de hombros hacia las orejas, mirada entre las manos, pelvis en retroversión."
    },
    {
        "id": "muscle-up",
        "name": "Bar Muscle-Up",
        "level": "Avanzado",
        "category": "Combinado (Pull + Push)",
        "target_muscles": ["Dorsal ancho", "Pectoral", "Tríceps", "Core"],
        "prerequisites": ["10-12 dominadas explosivas al pecho", "15 fondos en barra recta (straight bar dips)"],
        "progression_order": 3,
        "key_cues": "Tirón explosivo en arco hacia la cadera, transición rápida del torso sobre la barra inclinando los codos hacia adelante, y bloqueo final en fondo."
    },
    {
        "id": "front-lever",
        "name": "Front Lever",
        "level": "Avanzado",
        "category": "Tirón estático (Isometría)",
        "target_muscles": ["Dorsal ancho", "Redondo mayor", "Abdomen / Core anterior", "Tríceps (cabeza larga)"],
        "prerequisites": ["Tuck Front Lever (20s)", "Advanced Tuck Front Lever (15s)", "Dragon Flag (3x8)"],
        "progression_order": 4,
        "key_cues": "Brazos totalmente rectos, retracción y depresión escapular máxima, cuerpo paralelo al suelo en línea recta."
    },
    {
        "id": "planche",
        "name": "Full Planche",
        "level": "Élite",
        "category": "Empuje estático (Isometría)",
        "target_muscles": ["Deltoides anterior", "Pectoral mayor", "Bíceps (tendón distal)", "Core"],
        "prerequisites": ["Planche Lean estricta con bloqueo", "Tuck Planche (20s)", "Straddle Planche (10s)"],
        "progression_order": 5,
        "key_cues": "Inclinación pronunciada hacia adelante, protracción y depresión escapular activa, cadera a la altura de los hombros, glúteos contraídos."
    }
]

def seed():
    print(f"Connecting to Firestore for project '{PROJECT_ID}'...")
    collection_ref = db.collection("calisthenics_skills")
    for item in SKILLS_DATA:
        doc_ref = collection_ref.document(item["id"])
        doc_ref.set(item)
        print(f"Seeded: {item['name']} ({item['id']})")
    print("Seeding completed successfully!")

if __name__ == "__main__":
    seed()
