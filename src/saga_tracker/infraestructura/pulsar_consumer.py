import os, logging
import pulsar

logger = logging.getLogger(__name__)

class PulsarConfig:
    def __init__(self):
        self.service_url = os.getenv('PULSAR_SERVICE_URL', 'pulsar://localhost:6650')
        self.subscription = os.getenv('SUBSCRIPTION_NAME', 'saga-tracker')
        topics_env = os.getenv('TOPICS', 'campaigns/lifecycle')
        self.topics = [t.strip() for t in topics_env.split(',') if t.strip()]

class PulsarConsumers:
    def __init__(self, cfg: PulsarConfig):
        self.cfg = cfg
        self.client = pulsar.Client(self.cfg.service_url)
        self.consumer = self.client.subscribe(
            self.cfg.topics, 
            subscription_name=self.cfg.subscription, 
            consumer_type=pulsar.ConsumerType.KeyShared
        )

    def receive(self, timeout_millis=1000):
        try:
            return self.consumer.receive(timeout_millis=timeout_millis)
        except pulsar.Timeout:
            return None

    def acknowledge(self, msg):
        self.consumer.acknowledge(msg)

    def close(self):
        try:
            self.consumer.close()
        finally:
            self.client.close()
