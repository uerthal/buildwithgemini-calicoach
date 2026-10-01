# My agent: CaliCoach (Entrenador Personal de Calistenia)
One-liner: Un agente conversacional que guía a atletas y entusiastas de la calistenia en sus progresiones, rutinas y habilidades corporales con un catálogo de ejercicios, progresiones y técnicas.

Tool coverage:
- Memory: Nivel del atleta (principiante, intermedio, avanzado), habilidades desbloqueadas o en progreso (pull-ups, muscle-up, front lever, handstand, planche), lesiones/limitaciones articulares (muñecas, hombros) y equipamiento disponible (barra de dominadas, barras paralelas, anillas, suelo).
- Tools: Registro de sesiones y repeticiones/tiempos bajo tensión, consulta de progresiones por habilidad (roadmap escalonado hacia un movimiento objetivo), y recomendación de rutinas según nivel de fatiga.
- Catalog/UI: Catálogo de habilidades y progresiones de calistenia en tarjetas A2UI (nombre del ejercicio, nivel de dificultad, músculos implicados, técnica clave y prerrequisitos) y tabla de rutina diaria/semanal.
- Image gen: Generación de ilustraciones visuales con la técnica y alineación corporal correcta (ej. postura de hollow body, alineación del pino/handstand o agarre falso en anillas).
- Sandbox: Cálculo de volumen semanal de entrenamiento (series x reps x RPE), porcentaje de avance hacia una habilidad meta y balance de empuje vs tirón.

Recommended for every project: memory, storage, tools, image generation, A2UI
Agent-specific / stretch (pick what fits): Code sandbox para balance de volumen (push/pull ratio) y sobrecarga progresiva, Cloud Trace para observabilidad.
