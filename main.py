import logging
import os, json
from faker import Faker
from dotenv import load_dotenv


from confluent_kafka import SerializingProducer
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka.serialization import StringSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
import sys
import resource


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


load_dotenv(verbose=True)




# def startup_event():
#   client = AdminClient({'bootstrap.servers': os.environ['BOOTSTRAP_SERVERS']})
#   topic = NewTopic(os.environ['TOPICS_PEOPLE_AVRO_NAME'],
#                 num_partitions=int(os.environ['TOPICS_PEOPLE_AVRO_PARTITIONS']),
#                 replication_factor=int(os.environ['TOPICS_PEOPLE_AVRO_REPLICAS']))
#   try:
#     futures = client.create_topics([topic])
#     for topic_name, future in futures.items():
#       future.result()
#       logger.info(f"Create topic {topic_name}")
#   except Exception as e:
#     logger.warning(e)




def make_producer() -> SerializingProducer:
  # make a SchemaRegistryClient
  schema_reg_client = SchemaRegistryClient({'url': os.environ['SCHEMA_REGISTRY_URL']})


  # create AvroSerializer
  avro_serializer = AvroSerializer(schema_reg_client,
                                  resource.resource,
                                  )


  # create and return SerializingProducer
  return SerializingProducer({'bootstrap.servers': os.environ['BOOTSTRAP_SERVERS'],
                            'linger.ms': 300,
                            'enable.idempotence': 'true',
                            'max.in.flight.requests.per.connection': 1,
                            'acks': 'all',
                            'key.serializer': StringSerializer('utf_8'),
                            'value.serializer': avro_serializer,
                            'partitioner': 'murmur2_random'})




class ProducerCallback:
  def __init__(self, person):
    self.person = person


  def __call__(self, err, msg):
    if err:
      logger.error(f"Failed to produce {self.person}", exc_info=err)
    else:
      logger.info(f"""
        Successfully produced {self.person}
        to partition {msg.partition()}
        at offset {msg.offset()}
      """)






def create_people(count):
    producer = make_producer()
    fake = Faker()
    data = [
        {"name": fake.name(), "title": fake.job()} for _ in range(count)
    ]




    print(data, type(data))
    for i, person in enumerate(data):
        print(person)
        key =person.get("name", "IJ")
        value = person
        producer.produce(
            topic='resource',
            key=key,
            value=value,
            on_delivery=ProducerCallback(person)
        )
    producer.flush()




create_people(5000)