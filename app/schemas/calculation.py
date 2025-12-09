from enum import Enum
from pydantic import BaseModel, validator
from typing import List, Optional


class CalculationType(str, Enum):
    addition = "addition"
    subtraction = "subtraction"
    multiplication = "multiplication"
    division = "division"
    modulus = "modulus"


class CalculationBase(BaseModel):
    type: CalculationType
    inputs: List[float]

    @validator("inputs")
    def min_two_inputs(cls, v):
        if len(v) < 2:
            raise ValueError()
        return v


class CalculationCreate(CalculationBase):
    user_id: str

    @validator("inputs")
    def no_div_zero(cls, v, values):
        t = values.get("type")
        if t == CalculationType.division or t == CalculationType.modulus:
            if any(x == 0 for x in v[1:]):
                raise ValueError()
        return v


class CalculationUpdate(BaseModel):
    type: Optional[CalculationType]
    inputs: Optional[List[float]]
    user_id: Optional[str]


class CalculationResponse(CalculationBase):
    id: int
    user_id: str
    result: float
