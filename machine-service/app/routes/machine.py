from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from ..database import get_db
from ..models import Machine
from ..schemas import MachineCreate, MachineUpdate, MachineStatusUpdate, MachineResponse

router = APIRouter(prefix="/machines", tags=["Machines"])

VALID_STATUSES = {"running", "stopped", "maintenance"}


@router.get("/", response_model=List[MachineResponse], summary="Lister les machines")
def list_machines(
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    machine_type: Optional[str] = Query(None, description="Filtrer par type de machine"),
    db: Session = Depends(get_db),
):
    query = db.query(Machine)
    if status:
        query = query.filter(Machine.status == status)
    if machine_type:
        query = query.filter(Machine.machine_type == machine_type)
    return query.all()


@router.get("/{machine_id}", response_model=MachineResponse, summary="Détail d'une machine")
def get_machine(machine_id: int, db: Session = Depends(get_db)):
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail=f"Machine #{machine_id} introuvable")
    return machine


@router.post("/", response_model=MachineResponse, status_code=201, summary="Ajouter une machine")
def create_machine(payload: MachineCreate, db: Session = Depends(get_db)):
    # Vérifier l'unicité du numéro de série
    if payload.serial_number:
        existing = db.query(Machine).filter(Machine.serial_number == payload.serial_number).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Numéro de série '{payload.serial_number}' déjà utilisé par la machine #{existing.id}",
            )
    machine = Machine(**payload.model_dump())
    db.add(machine)
    db.commit()
    db.refresh(machine)
    return machine


@router.put("/{machine_id}/status", response_model=MachineResponse, summary="Changer le statut d'une machine")
def update_machine_status(machine_id: int, payload: MachineStatusUpdate, db: Session = Depends(get_db)):
    if payload.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Statut invalide. Valeurs acceptées : {sorted(VALID_STATUSES)}",
        )
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail=f"Machine #{machine_id} introuvable")

    # Si on passe en maintenance, on enregistre la date
    if payload.status == "maintenance":
        machine.last_maintenance_at = datetime.now(timezone.utc)

    machine.status = payload.status
    machine.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(machine)
    return machine


@router.patch("/{machine_id}", response_model=MachineResponse, summary="Modifier les infos d'une machine")
def update_machine(machine_id: int, payload: MachineUpdate, db: Session = Depends(get_db)):
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail=f"Machine #{machine_id} introuvable")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(machine, field, value)
    machine.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(machine)
    return machine


@router.delete("/{machine_id}", status_code=204, summary="Supprimer une machine")
def delete_machine(machine_id: int, db: Session = Depends(get_db)):
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail=f"Machine #{machine_id} introuvable")
    if machine.status == "running":
        raise HTTPException(status_code=409, detail="Impossible de supprimer une machine en cours d'exécution")
    db.delete(machine)
    db.commit()
