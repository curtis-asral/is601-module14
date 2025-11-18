from app.schemas.calculation import CalculationCreate, CalculationType
import pytest

def test_valid_addition():
    data = {"type": CalculationType.addition, "inputs": [1,2], "user_id": 1}
    obj = CalculationCreate(**data)
    assert obj.type == CalculationType.addition

def test_min_two_inputs():
    data = {"type": CalculationType.addition, "inputs": [1], "user_id": 1}
    with pytest.raises(ValueError):
        CalculationCreate(**data)

def test_division_by_zero():
    data = {"type": CalculationType.division, "inputs": [8,0], "user_id": 1}
    with pytest.raises(ValueError):
        CalculationCreate(**data)
