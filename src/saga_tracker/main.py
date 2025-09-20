import logging, os, threading, time
from flask import Flask, jsonify
from saga_tracker.config.db import init_db
from saga_tracker.infraestructura.tracker_service import SagaTrackerService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)

    database_url = os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:postgres@localhost:5432/saga_db')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    @app.get("/health")
    def health():
        return jsonify(status="ok"), 200

    init_db(app)
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
