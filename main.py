from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.calculation import Calculation
from app.schemas.base import UserCreate, UserLogin
from app.schemas.user import UserResponse, Token
from app.schemas.calculation import (
    CalculationCreate,
    CalculationResponse,
    CalculationUpdate,
)
import uvicorn
import logging
from app.operations import add, subtract, multiply, divide
from app.database import engine, Base
Base.metadata.create_all(bind=engine)

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

    @field_validator("a", "b")  # Correct decorator for Pydantic 1.x
    def validate_numbers(cls, value):
        if not isinstance(value, (int, float)):
            raise ValueError("Both a and b must be numbers.")
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
    error_messages = "; ".join(
        [f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors()]
    )
    logger.error(f"ValidationError on {request.url.path}: {error_messages}")
    return JSONResponse(status_code=400, content={"error": error_messages})


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# User Endpoints
@app.post("/users/register")
async def register_user(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    user_data = {
        "first_name": form.get("first_name"),
        "last_name": form.get("last_name"),
        "email": form.get("email"),
        "username": form.get("username"),
        "password": form.get("password"),
    }
    db_user = (
        db.query(User)
        .filter(
            (User.email == user_data["email"])
            | (User.username == user_data["username"])
        )
        .first()
    )
    if db_user:
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "User already exists."}
        )
    hashed = User.hash_password(user_data["password"])
    new_user = User(**user_data, password=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return RedirectResponse("/login", status_code=HTTP_303_SEE_OTHER)


@app.post("/users/login")
async def login_user(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user or not db_user.verify_password(password):
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Invalid credentials."}
        )
    token = User.create_access_token({"sub": str(db_user.id)})
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "success": "Logged in!", "token": token, "user": db_user},
    )


# Calculation Endpoints (BREAD)
from app.auth.dependencies import get_current_active_user

@app.get("/calculations")
async def browse_calculations(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    items = db.query(Calculation).filter(Calculation.user_id == current_user.id).all()
    return templates.TemplateResponse(
        "calculations.html", {"request": request, "calculations": items}
    )


@app.get("/calculations/{id}", response_model=CalculationResponse)
def read_calculation(
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    i = db.query(Calculation).filter(Calculation.id == id, Calculation.user_id == current_user.id).first()
    if not i:
        raise HTTPException(status_code=404)
    return CalculationResponse(
        id=i.id,
        user_id=str(i.user_id),
        type=i.type,
        inputs=i.inputs,
        result=i.get_result(),
    )


@app.post("/calculations")
async def add_calculation(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    form = await request.form()
    calc_type = form.get("type")
    inputs = [float(x.strip()) for x in form.get("inputs", "").split(",") if x.strip()]
    obj = Calculation.create(calc_type, current_user.id, inputs)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return RedirectResponse("/calculations", status_code=HTTP_303_SEE_OTHER)


@app.put("/calculations/{id}", response_model=CalculationResponse)
def edit_calculation(
    id: int,
    calc: CalculationUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    obj = db.query(Calculation).filter(Calculation.id == id, Calculation.user_id == current_user.id).first()
    if not obj:
        raise HTTPException(status_code=404)
    if calc.type:
        obj.type = calc.type.value
    if calc.inputs:
        obj.inputs = calc.inputs
    db.commit()
    db.refresh(obj)
    return CalculationResponse(
        id=obj.id,
        user_id=str(obj.user_id),
        type=obj.type,
        inputs=obj.inputs,
        result=obj.get_result(),
    )


@app.delete("/calculations/{id}")
def delete_calculation(
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    obj = db.query(Calculation).filter(Calculation.id == id, Calculation.user_id == current_user.id).first()
    if not obj:
        raise HTTPException(status_code=404)
    db.delete(obj)
    db.commit()
    return {"ok": True}


@app.post(
    "/add", response_model=OperationResponse, responses={400: {"model": ErrorResponse}}
)
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


@app.post(
    "/subtract",
    response_model=OperationResponse,
    responses={400: {"model": ErrorResponse}},
)
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


@app.post(
    "/multiply",
    response_model=OperationResponse,
    responses={400: {"model": ErrorResponse}},
)
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


@app.post(
    "/divide",
    response_model=OperationResponse,
    responses={400: {"model": ErrorResponse}},
)
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
