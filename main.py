from fastapi import FastAPI
from contextlib import asynccontextmanager

import asyncio

from stimulate import (
    prediction_loop,
    bounded_memory,
    metrics,
    run_once as execute_prediction
)

from datetime import datetime, timedelta


@asynccontextmanager 
async def lifespan(app: FastAPI):
    task = asyncio.create_task(prediction_loop())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)



@app.post("/run-once_endpoint")
def run_once_endpoint():
    execute_prediction()
    return {"message": "prediction executed"}




print("health")
@app.get('/health')

def health():
    if not bounded_memory:
        return {
            "status":"Not started"
        }
    
    last_prediction_time = bounded_memory[-1]["prediction_time"]
    time_diff = datetime.now() - last_prediction_time

    if time_diff <= timedelta(seconds=60):
        return {
            "status": "running",
            "last_model_run_time": last_prediction_time
        }
    
    else:
        return {
            "status":"inactive"
        }
    


print("prediction")
@app.get('/prediction')
def model_prediction():
    #latest prediction + timestamps -> last element of bounded memory 
    if not bounded_memory:
        return {"message":"no prediction yet"}
    
    latest = bounded_memory[-1]

    return latest

@app.get("/metrics")
def get_metrics():
    return metrics


    
