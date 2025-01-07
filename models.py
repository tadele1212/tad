from typing import List
from pydantic import BaseModel

class ServiceInput(BaseModel):
    service_no: str

class NearestStopInput(BaseModel):
    service_no: str
    gx: float
    gy: float
    last_stop: int

class Stop(BaseModel):
    Seq: int
    Bus_Stop: str
    KM: float

class StopResponse(BaseModel):
    stops: List[Stop]