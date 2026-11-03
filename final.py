# =========================
# IMPORTS
# =========================
import asyncio
import time
import random
import pickle
from collections import deque
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional


# =========================
# DATA MODELS
# =========================
class SensorReading(BaseModel):
    PT08_S1_CO: float
    C6H6_GT: float
    PT08_S2_NMHC: float
    NOx_GT: float
    PT08_S3_NOx: float
    NO2_GT: float
    PT08_S4_NO2: float
    PT08_S5_O3: float
    Temp: float
    RH: float
    AH: float
    timestamp: datetime


class Prediction(BaseModel):
    timestamp: datetime
    predicted_value: float
    result: Optional[str] = None


# =========================
# SENSOR SIMULATOR
# =========================
class SensorSimulator:
    @staticmethod
    def generate() -> SensorReading:
        return SensorReading(
            PT08_S1_CO=random.uniform(600, 2050),
            C6H6_GT=random.uniform(0, 65),
            PT08_S2_NMHC=random.uniform(380, 2250),
            NOx_GT=random.uniform(0, 1500),
            PT08_S3_NOx=random.uniform(300, 2700),
            NO2_GT=random.uniform(0, 300),
            PT08_S4_NO2=random.uniform(500, 2700),
            PT08_S5_O3=random.uniform(200, 2500),
            Temp=random.uniform(-10, 50),
            RH=random.uniform(0, 90),
            AH=random.uniform(0, 50),
            timestamp=datetime.now()
        )


# =========================
# MODEL SERVICE
# =========================
class ModelService:
    def __init__(self, model_path: str):
        with open(model_path, "rb") as f:
            self.model = pickle.load(f)

    def predict(self, sensor: SensorReading) -> float:
        df = pd.DataFrame({
            "PT08.S1(CO)": sensor.PT08_S1_CO,
            "C6H6(GT)": sensor.C6H6_GT,
            "PT08.S2(NMHC)": sensor.PT08_S2_NMHC,
            "NOx(GT)": sensor.NOx_GT,
            "PT08.S3(NOx)": sensor.PT08_S3_NOx,
            "NO2(GT)": sensor.NO2_GT,
            "PT08.S4(NO2)": sensor.PT08_S4_NO2,
            "PT08.S5(O3)": sensor.PT08_S5_O3,
            "T": sensor.Temp,
            "RH": sensor.RH,
            "AH": sensor.AH
        }, index=[0])

        return self.model.predict(df)[0]


# =========================
# STATE (MEMORY + METRICS)
# =========================
class PredictionState:
    def __init__(self, max_len: int = 10):
        self.memory = deque(maxlen=max_len)
        self.metrics = {
            "run_count": 0,
            "last_run_time": None,
            "avg_duration": 0.0
        }

    def update(self, sensor: SensorReading, prediction: float, duration: float):
        self.memory.append({
            "stimulated_timestamp": sensor.timestamp,
            "stimulated_values": sensor.model_dump(),
            "predicted_value": prediction,
            "prediction_time": datetime.now()
        })

        self.metrics["run_count"] += 1
        self.metrics["last_run_time"] = datetime.now()
        self.metrics["avg_duration"] = (
            (self.metrics["avg_duration"] * (self.metrics["run_count"] - 1) + duration)
            / self.metrics["run_count"]
        )


# =========================
# PREDICTION ENGINE
# =========================
class PredictionEngine:
    def __init__(self):
        self.simulator = SensorSimulator()
        self.model_service = ModelService("model.pkl")
        # self.model_service = ModelService("Backend/model.pkl")
        self.state = PredictionState()

    def run_once(self):
        start = time.time()

        sensor = self.simulator.generate()
        prediction = self.model_service.predict(sensor)

        duration = time.time() - start
        self.state.update(sensor, prediction, duration)


engine = PredictionEngine()


# =========================
# BACKGROUND LOOP
# =========================
async def prediction_loop():
    while True:
        engine.run_once()
        await asyncio.sleep(60)


# =========================
# FASTAPI LIFESPAN
# =========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(prediction_loop())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)


# =========================
# API ENDPOINTS
# =========================
@app.get("/health")
def health():
    if not engine.state.memory:
        return {"status": "not started"}

    last_time = engine.state.memory[-1]["prediction_time"]
    if datetime.now() - last_time <= timedelta(seconds=60):
        return {"status": "running", "last_run": last_time}
    return {"status": "inactive"}


@app.get("/prediction")
def get_prediction():
    if not engine.state.memory:
        return {"message": "no prediction yet"}
    return engine.state.memory[-1]


@app.get("/metrics")
def get_metrics():
    return engine.state.metrics
