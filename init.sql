-- Script de inicialización de la base de datos para SAGA LOG

CREATE TABLE IF NOT EXISTS saga_instance (
    saga_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_key UUID NOT NULL,
    type VARCHAR(255) NOT NULL,
    status VARCHAR(255) NOT NULL,
    started_at VARCHAR(500) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_event_id INT NOT NULL,
    retries_total INT NOT NULL
);

CREATE TABLE IF NOT EXISTS saga_step (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    saga_id UUID NOT NULL,
    seq INT NOT NULL,
    event_id UUID NOT NULL,
    topic  VARCHAR(250) NOT NULL,
    service VARCHAR(250) NOT NULL,
    step VARCHAR(250) NOT NULL DEFAULT 'registrado',
    status  VARCHAR(250) NOT NULL,
    payload TEXT NOT NULL,
    ts_event TIMESTAMP NOT NULL,
    ts_ingested TIMESTAMP NOT NULL
);
