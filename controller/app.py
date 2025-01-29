from fastapi import FastAPI, Request, Response
import logging
import json
# from pymongo import MongoClient
import asyncio
import aiormq
import os
import uvicorn

RABBITMQ_URL = "amqp://user:password@rabbitmq/"
RABBIT_TASK_QUEUE_NAME = "queue"

# MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
# client = MongoClient(MONGO_URI)
# db = client["mydatabase"]
# collection = db["data"]

logging.basicConfig(
    filename='/var/log/controller.log',
    level=logging.INFO,
    format='%(name)s - %(levelname)s - %(message)s',
    filemode='a'
)

app = FastAPI()

async def send_message(json_body):
    try:
        connection = await aiormq.connect(RABBITMQ_URL)
        channel = await connection.channel()

        await channel.basic_publish(
            exchange="",
            routing_key=RABBIT_TASK_QUEUE_NAME,
            body=json_body)

        logging.info(f"Sent message: {json_body}")

        await connection.close()

    except aiormq.AMQPConnectionError as e:
        logging.error("Error while connecting to RabbitMQ", exc_info=e)
        await asyncio.sleep(2)

@app.post("/api/data")
async def receive_data(request: Request):
    json_data = await request.body()
    d = json.loads(json_data)

    response = Response()
    response.status_code = 200

    if d["A"] < 2:
        logging.warning(f"Data dropped: {d}")
        return response

    # idk do we need to store something from this service ?
    # collection.insert_one(d)
    # print("Data saved to mongo")

    await send_message(json_data)

    logging.info(f"Data forwarded: {d}")
    return response

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)