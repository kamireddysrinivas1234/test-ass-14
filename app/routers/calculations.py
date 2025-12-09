from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import schemas, crud_calculations, models
from ..dependencies import get_db, get_current_user

router = APIRouter(prefix="/calculations", tags=["calculations"])

@router.get("/", response_model=List[schemas.CalculationRead])
def browse(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return crud_calculations.browse_calculations(db, user_id=user.id)

@router.post("/", response_model=schemas.CalculationRead, status_code=status.HTTP_201_CREATED)
def add(calc_in: schemas.CalculationCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return crud_calculations.create_calculation(db, calc_in, user_id=user.id)

@router.get("/{calc_id}", response_model=schemas.CalculationRead)
def read(calc_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    calc = crud_calculations.get_calculation(db, calc_id)
    if not calc or calc.user_id != user.id:
        raise HTTPException(status_code=404, detail="Calculation not found")
    return calc

@router.put("/{calc_id}", response_model=schemas.CalculationRead)
@router.patch("/{calc_id}", response_model=schemas.CalculationRead)
def edit(calc_id: int, update: schemas.CalculationUpdate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    calc = crud_calculations.get_calculation(db, calc_id)
    if not calc or calc.user_id != user.id:
        raise HTTPException(status_code=404, detail="Calculation not found")

    # Division by zero guard for updates
    new_type = update.type.value if update.type else calc.type
    new_b = update.b if update.b is not None else calc.b
    if new_type == "div" and new_b == 0:
        raise HTTPException(status_code=422, detail="b cannot be zero for division")

    return crud_calculations.update_calculation(db, calc, update)

@router.delete("/{calc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(calc_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    calc = crud_calculations.get_calculation(db, calc_id)
    if not calc or calc.user_id != user.id:
        raise HTTPException(status_code=404, detail="Calculation not found")
    crud_calculations.delete_calculation(db, calc)
    return None
