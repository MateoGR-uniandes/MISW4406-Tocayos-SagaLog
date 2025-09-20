# Saga Tracker (Consumer) – Pulsar + SQLAlchemy

Microservicio **consumer** que actúa como **Saga Log** pasivo:
- Se suscribe a tópicos de Pulsar
- Persiste pasos de saga (`saga_step`) e instancia (`saga_instance`) con **SQLAlchemy**
- No emite comandos ni decide el flujo (coreografiación pura)

## Variables de entorno

- `DATABASE_URL` (ej. `postgresql+psycopg2://postgres:postgres@localhost:5432/saga_db`)
- `PULSAR_SERVICE_URL` (ej. `pulsar://localhost:6650`)
- `SUBSCRIPTION_NAME` (ej. `saga-tracker`)
- `TOPICS` (lista separada por coma; ej. `loyalty/program,campaigns/lifecycle,content/search,partner/association`)

## Run local

```bash
pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/saga_db
export PULSAR_SERVICE_URL=pulsar://localhost:6650
python src/saga_tracker/main.py
```

## Docker

```bash
docker compose up --build
```

