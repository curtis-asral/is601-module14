# main.py

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.calculation import Calculation
from app.schemas.base import UserCreate, UserLogin
from app.schemas.user import UserResponse, Token
from app.schemas.calculation import CalculationCreate, CalculationResponse, CalculationUpdate
import uvicorn
import logging
from app.operations import add, subtract, multiply, divide

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Setup templates directory
templates = Jinja2Templates(directory="templates")

# Pydantic model for request data
class OperationRequest(BaseModel):
    a: float = Field(..., description="The first number")
    b: float = Field(..., description="The second number")

    @field_validator('a', 'b')  # Correct decorator for Pydantic 1.x
    def validate_numbers(cls, value):
        if not isinstance(value, (int, float)):
            raise ValueError('Both a and b must be numbers.')
        return value

# Pydantic model for successful response
class OperationResponse(BaseModel):
    result: float = Field(..., description="The result of the operation")

# Pydantic model for error response
class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTPException on {request.url.path}: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_messages = "; ".join([f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors()])
    logger.error(f"ValidationError on {request.url.path}: {error_messages}")
    return JSONResponse(status_code=400, content={"error": error_messages})

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# User Endpoints
@app.post("/users/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter((User.email == user.email) | (User.username == user.username)).first()
    if db_user:
        raise HTTPException(status_code=400)
    hashed = User.hash_password(user.password)
    new_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        username=user.username,
        password=hashed
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/users/login", response_model=Token)
def login_user(login: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == login.username).first()
    if not db_user or not db_user.verify_password(login.password):
        raise HTTPException(status_code=401)
    token = User.create_access_token({"sub": str(db_user.id)})
    return Token(access_token=token, user=db_user)

# Calculation Endpoints (BREAD)
@app.get("/calculations", response_model=list[CalculationResponse])
def browse_calculations(db: Session = Depends(get_db)):
    items = db.query(Calculation).all()
    return [CalculationResponse(
        id=i.id,
        user_id=str(i.user_id),
        type=i.type,
        inputs=i.inputs,
        result=i.get_result()
    ) for i in items]

@app.get("/calculations/{id}", response_model=CalculationResponse)
def read_calculation(id: int, db: Session = Depends(get_db)):
    i = db.query(Calculation).filter(Calculation.id == id).first()
    if not i:
        raise HTTPException(status_code=404)
    return CalculationResponse(
        id=i.id,
        user_id=str(i.user_id),
        type=i.type,
        inputs=i.inputs,
        result=i.get_result()
    )

@app.post("/calculations", response_model=CalculationResponse)
def add_calculation(calc: CalculationCreate, db: Session = Depends(get_db)):
    obj = Calculation.create(calc.type.value, calc.user_id, calc.inputs)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return CalculationResponse(
        id=obj.id,
        user_id=str(obj.user_id),
        type=obj.type,
        inputs=obj.inputs,
        result=obj.get_result()
    )

@app.put("/calculations/{id}", response_model=CalculationResponse)
def edit_calculation(id: int, calc: CalculationUpdate, db: Session = Depends(get_db)):
    obj = db.query(Calculation).filter(Calculation.id == id).first()
    if not obj:
        raise HTTPException(status_code=404)
    if calc.type:
        obj.type = calc.type.value
    if calc.inputs:
        obj.inputs = calc.inputs
    if calc.user_id:
        obj.user_id = calc.user_id
    db.commit()
    db.refresh(obj)
    return CalculationResponse(
        id=obj.id,
        user_id=str(obj.user_id),
        type=obj.type,
        inputs=obj.inputs,
        result=obj.get_result()
    )

@app.delete("/calculations/{id}")
def delete_calculation(id: int, db: Session = Depends(get_db)):
    obj = db.query(Calculation).filter(Calculation.id == id).first()
    if not obj:
        raise HTTPException(status_code=404)
    db.delete(obj)
    db.commit()
    return {"ok": True}

@app.post("/add", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def add_route(operation: OperationRequest):
    """
    Add two numbers.
    """
    try:
        result = add(operation.a, operation.b)
        return OperationResponse(result=result)
    except Exception as e:
        logger.error(f"Add Operation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/subtract", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def subtract_route(operation: OperationRequest):
    """
    Subtract two numbers.
    """
    try:
        result = subtract(operation.a, operation.b)
        return OperationResponse(result=result)
    except Exception as e:
        logger.error(f"Subtract Operation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/multiply", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def multiply_route(operation: OperationRequest):
    """
    Multiply two numbers.
    """
    try:
        result = multiply(operation.a, operation.b)
        return OperationResponse(result=result)
    except Exception as e:
        logger.error(f"Multiply Operation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/divide", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def divide_route(operation: OperationRequest):
    """
    Divide two numbers.
    """
    try:
        result = divide(operation.a, operation.b)
        return OperationResponse(result=result)
    except ValueError as e:
        logger.error(f"Divide Operation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Divide Operation Internal Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
