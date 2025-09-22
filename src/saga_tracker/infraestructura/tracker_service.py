import json, logging
from datetime import datetime
from typing import Any, Dict, Tuple
import uuid
from saga_tracker.infraestructura.pulsar_consumer  import PulsarConfig, PulsarConsumers
from saga_tracker.config.db import db
from models.saga_models import SagaInstance, SagaStep
from sqlalchemy import func, select

logger = logging.getLogger(__name__)

class SagaTrackerService:
    def __init__(self, app=None):
        self.app = app
        self.cfg = PulsarConfig()
        self.consumers = None
        self.running = False

    def start(self):
        self.consumers = PulsarConsumers(self.cfg)
        self.running = True
        logger.info(f"SagaTracker escuchando tópicos: {self.cfg.topics}")

    def stop(self):
        self.running = False
        if self.consumers:
            self.consumers.close()

    def _next_seq(self, saga_id: str) -> int:
        with self.app.app_context():
            res = db.session.execute(
                select(func.coalesce(func.max(SagaStep.seq), 0)).where(SagaStep.saga_id == saga_id)
            ).scalar_one()
            return int(res) + 1

    def _upsert_instance(self, saga_id: str, business_key: str | None, type_: str, new_status: str, event_id: str):
        with self.app.app_context():
            si = db.session.get(SagaInstance, saga_id)
            if si is None:
                si = SagaInstance(
                    saga_id=saga_id, 
                    business_key=business_key, 
                    type=type_, 
                    status=new_status, 
                    started_at=datetime.utcnow(), 
                    updated_at=datetime.utcnow(), 
                    last_event_id=event_id
                )
                db.session.add(si)
            else:
                si.status = new_status
                si.updated_at = datetime.utcnow()
                si.last_event_id = event_id
            db.session.commit()

    def _transition(self, step: str, step_status: str) -> str:
        if step.endswith('Completed') and step_status.lower() == 'success':
            return 'Completed'
        if step_status.lower() == 'failed':
            return 'Compensating'
        return 'InProgress'

    def tick(self):
        if not self.running:
            return
        msg = self.consumers.receive(1000)
        if not msg:
            return
        try:
            payload = json.loads(msg.data())
            headers = payload
            saga_id = headers.get('saga_id') or headers.get('correlation_id') or 'unknown'
            event_id = headers.get('event_id') or uuid.uuid4()
            event_type = headers.get('event_type', 'unknown')
            event_data = headers.get('event_data', 'unknown')
            service = headers.get('service', 'unknown')
            ts = headers.get('timestamp')
            try:
                ts_event = datetime.fromisoformat(ts.replace('Z','+00:00')) if isinstance(ts, str) else datetime.utcnow()
            except Exception:
                ts_event = datetime.utcnow()
            step_status = headers.get('status', 'Success' if 'failed' not in event_type else 'Failed')
            business_key = event_id#payload.get('payload', {}).get('id')
            saga_type = event_type

            with self.app.app_context():
                seq = self._next_seq(saga_id)
                st = SagaStep(
                    saga_id=saga_id,
                    seq=seq,
                    event_id=event_id,
                    # causation_id=headers.get('causation_id'),
                    topic=str(msg.topic_name().decode() if hasattr(msg.topic_name(), 'decode') else msg.topic_name()),
                    service=service,
                    step=event_type,
                    status=step_status,
                    payload=event_data,
                    # error_code=payload.get('payload', {}).get('reasonCode'),
                    # error_msg=payload.get('payload', {}).get('reasonMsg'),
                    ts_event=ts_event
                )
                db.session.add(st)
                db.session.commit()

            new_status = self._transition(event_type, step_status)
            self._upsert_instance(saga_id, business_key, saga_type, new_status, seq)

            self.consumers.acknowledge(msg)
        except Exception as e:
            logger.exception("Error procesando mensaje del SagaTracker: %s", e)
            # No ack

    def get_by_saga_id(self, saga_id: str, include_steps: bool = True, limit: int = 100, offset: int = 0) -> Tuple[Dict[str, Any], int]:
        """
        Consulta la saga en BD y devuelve (payload_json, http_status).
        Diseñado para ser llamado desde main.py en el endpoint HTTP.
        """
        with self.app.app_context():
            inst = db.session.get(SagaInstance, saga_id)
            if inst is None:
                return {"error": "not_found", "sagaId": saga_id}, 404

            result = {
                "instance": {
                    "sagaId": inst.saga_id,
                    "businessKey": inst.business_key,
                    "type": inst.type,
                    "status": inst.status,
                    "startedAt": inst.started_at,
                    "updatedAt": inst.updated_at,
                    "lastEventId": inst.last_event_id,
                    "retriesTotal": inst.retries_total,
                }
            }

            if include_steps:
                stmt = (
                    select(SagaStep)
                    .where(SagaStep.saga_id == saga_id)
                    .order_by(SagaStep.seq.asc())
                    .offset(offset)
                    .limit(max(1, min(limit, 1000)))
                )
                steps = db.session.execute(stmt).scalars().all()
                result["steps"] = [{
                    "id": s.id,
                    "seq": s.seq,
                    "eventId": s.event_id,
                    "topic": s.topic,
                    "service": s.service,
                    "eventType": s.step,
                    "status": s.status,
                    "payload": s.payload,
                    "tsEvent": s.ts_event if s.ts_event else None,
                    "tsIngested": s.ts_ingested if s.ts_ingested else None,
                } for s in steps]
                result["pagination"] = {"limit": limit, "offset": offset, "returned": len(steps)}

            return result, 200
        
#
# {
# "event_type": "ProgramaLealtadRegistrado",
# "event_data": {
# "id": "567fc4f7-3efd-4c47-a6c1-b9b11a0c4e3e",
# "fecha_evento": "2025-09-20 13:37:11.806471",
# "tipo": "programa_lealtad_registrado",
# "categoria": "categoria test",
# "marca": "7e57a142-0a56-4006-bf4a-73bd3333f3c6",
# "audiencia": "audiencia test",
# "canales": "canales test",
# "inicio_campania": "2025-01-01 00:00:00",
# "final_campania": "2029-01-01 23:59:59"
# },
# "timestamp": "2025-09-20T13:37:11.806471"
# }