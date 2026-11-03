import os
import asyncio
from fastapi import FastAPI 
from pydantic import BaseModel,Field
from datetime import datetime
from typing import Optional
import random , pickle 
import pandas as pd 
from collections import deque
import time




#step 1 - define the struture  of sensor readings 

class SensorReading(BaseModel):

    #INPUT FEATURES -> may need to change as per constraits 

    PT08_S1_CO : float = Field(strict= True)
    C6H6_GT: float
    PT08_S2_NMHC : float
    NOx_GT: float
    PT08_S3_NOx : float
    NO2_GT: float
    PT08_S4_NO2:float 
    PT08_S5_O3:float
    Temp : float
    RH: float
    AH: float

    #Error - datetime - str --datetime.now().strftime("%Y-%m-%d %H:%M:%S") # type: ignore 
    timestamp:datetime

print("Sensor Reading working ")    

#predicted value - ML 
class Prediction(BaseModel):

    timestamp: datetime
    predicted_value : float
    Result: Optional[str] = None  #Optional -> Good or Bad , decide by  function 


print("Prediction  Reading working ")    




#function that stimulate inputs 

def generate_sensor_reading():

   
   stimulate_reading = SensorReading( PT08_S1_CO = random.uniform(600,2050),
    C6H6_GT = random.uniform(0,65),
    PT08_S2_NMHC = random.uniform(380,2250),
    NOx_GT = random.uniform(0,1500),
    PT08_S3_NOx  = random.uniform(300,2700),
    NO2_GT = random.uniform(0,300),
    PT08_S4_NO2 = random.uniform(500,2700),
    PT08_S5_O3 = random.uniform(200,2500),
    Temp = random.uniform(-10,50),
    RH = random.uniform(0,90),
    AH = random.uniform(0,50),
    timestamp = datetime.now()

    )

    
   
   return stimulate_reading
   

# generate_sensor_reading - function call

# print(reading)







print("features")

#STEP -2 MODEL LOAD AND PREDICT VALUE 
# with open('Backend/model.pkl','rb') as f:

#     model = pickle.load(f)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

print("model load")










# prediction object 

# print(result)

print("prediction object working ")

#step -3 Bounded memory 

Max_len= 10

# input_features , timestamp , prediction , prediction_time 

 

#Sensor Reading - N (1)

bounded_memory = deque(maxlen = Max_len)

metrics = {
    "run_count": 0,
    "last_run_time": None,
    "avg_duration": 0.0
}





def run_once():

    #generate sensor data 

    start_time = time.time()

    sensor_data = generate_sensor_reading()

    #values converted into dataframe
    input_features = pd.DataFrame({ "PT08.S1(CO)":sensor_data.PT08_S1_CO,
    "C6H6(GT)":sensor_data.C6H6_GT,
    "PT08.S2(NMHC)":sensor_data.PT08_S2_NMHC,
    "NOx(GT)":sensor_data.NOx_GT,
    "PT08.S3(NOx)":sensor_data.PT08_S3_NOx,
    "NO2(GT)":sensor_data.NO2_GT,
    "PT08.S4(NO2)":sensor_data.PT08_S4_NO2,
    "PT08.S5(O3)":sensor_data.PT08_S5_O3,
    "T":sensor_data.Temp,
    "RH":sensor_data.RH,
    "AH":sensor_data.AH

}, index = [0])
    
    #model predict 
    prediction = model.predict(input_features)[0]

    #predict object 
    result = Prediction(timestamp = datetime.now(),predicted_value= prediction)  

    #Bounded memory 
    # bounded_memory.append({"stimulate_timestamp":sensor_data.timestamp,
    #                    "stimulate_value":sensor_data.model_dump(),
    #                    "predict_value":result.predicted_value,
    #                    "prediction_time":result.timestamp})

    bounded_memory.append({
    "stimulated_timestamp": sensor_data.timestamp,
    "stimulated_values": sensor_data.model_dump(),
    "predicted_value": result.predicted_value,
    "prediction_time": result.timestamp
})

    
     # Update metrics 
    duration = time.time() - start_time
    metrics["run_count"] += 1
    metrics["last_run_time"] = datetime.now()
    # Update running average
    metrics["avg_duration"] = ((metrics["avg_duration"] * (metrics["run_count"] - 1)) + duration) / metrics["run_count"]
    

async def prediction_loop():
    while True:
        run_once()
        await asyncio.sleep(60)





    


    

  

















                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        












     










