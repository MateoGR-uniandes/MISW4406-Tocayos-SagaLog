import logging, os, threading, time
from flask import Flask, jsonify, request
from saga_tracker.config.db import init_db, db
from saga_tracker.infraestructura.tracker_service import SagaTrackerService
# REMOVE these imports from the top level
# from saga_tracker.models.saga_models import SagaInstance, SagaStep
from sqlalchemy import select


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    database_url = os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:postgres@localhost:5432/saga_db')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # Initialize db FIRST
    init_db(app)
    # NOW import models after db is initialized with app
    from saga_tracker.models.saga_models import SagaInstance, SagaStep
    @app.get("/health")
    def health():
        return jsonify(status="ok"), 200
    

    @app.get("/sagas/<string:saga_id>")
    def get_saga(saga_id):
        """
        Devuelve la información de una saga:
          - Objeto 'instance' (estado agregado)
          - Lista 'steps' (ordenados por seq ASC)
        Parámetros opcionales:
          - includeSteps=false|true  (default: true)
          - limit=<n> (default: 100)
          - offset=<n> (default: 0)
        """
        include_steps = (request.args.get("includeSteps", "true").lower() == "true")
        try:
            limit = int(request.args.get("limit", "100"))
            offset = int(request.args.get("offset", "0"))
            limit = max(1, min(limit, 1000))
            offset = max(0, offset)
        except ValueError:
            return jsonify({"error": "bad_request", "details": "limit/offset inválidos"}), 400
        inst = db.session.get(SagaInstance, saga_id)
        if inst is None:
            return jsonify({"error": "not_found", "sagaId": saga_id}), 404
        instance_dict = {
            "sagaId": inst.saga_id,
            "businessKey": inst.business_key,
            "type": inst.type,
            "status": inst.status,
            "startedAt": inst.started_at.isoformat() if inst.started_at else None,
            "updatedAt": inst.updated_at.isoformat() if inst.updated_at else None,
            "lastEventId": inst.last_event_id,
            "retriesTotal": inst.retries_total,
        }
        result = {"instance": instance_dict}
        if include_steps:
            stmt = (
                select(SagaStep)
                .where(SagaStep.saga_id == saga_id)
                .order_by(SagaStep.seq.asc())
                .offset(offset)
                .limit(limit)
            )
            steps = db.session.execute(stmt).scalars().all()
            result["steps"] = [{
                "id": s.id,
                "seq": s.seq,
                "eventId": s.event_id,
                "causationId": s.causation_id,
                "topic": s.topic,
                "service": s.service,
                "eventType": s.step,
                "status": s.status,
                "payload": s.payload,
                "errorCode": s.error_code,
                "errorMsg": s.error_msg,
                "tsEvent": s.ts_event.isoformat() if s.ts_event else None,
                "tsIngested": s.ts_ingested.isoformat() if s.ts_ingested else None,
            } for s in steps]
            result["pagination"] = {"limit": limit, "offset": offset, "returned": len(steps)}
        return jsonify(result), 200
    
    tracker = SagaTrackerService(app)
    tracker.start()

    def bg_loop():
        while True:
            try:
                tracker.tick()
            except Exception as e:
                logger.error("Error en loop del tracker: %s", e)
            time.sleep(0.05)

    t = threading.Thread(target=bg_loop, daemon=True)
    t.start()
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5010")), debug=True)