from fastapi import APIRouter, HTTPException, status, Depends
from app.principals.schemas import PrincipalResponse, PrincipalUpdate
from app.principals.crud import get_principal_by_user_id, update_principal
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/principals", tags=["principals"])

@router.get("/me", response_model=PrincipalResponse)
async def get_my_principal_data(current_user = Depends(get_current_user)):
    """Get current user's principal data"""
    principal = await get_principal_by_user_id(current_user.id)
    
    if not principal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Principal data not found"
        )
    
    return principal

@router.put("/me", response_model=PrincipalResponse)
async def update_my_principal_data(
    principal_data: PrincipalUpdate,
    current_user = Depends(get_current_user)
):
    """Update current user's principal data"""
    # Check if principal record exists
    existing_principal = await get_principal_by_user_id(current_user.id)
    
    if not existing_principal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Principal data not found"
        )
    
    # Update principal data
    updated_principal = await update_principal(current_user.id, principal_data)
    return updated_principal

@router.get("/{user_id}", response_model=PrincipalResponse)
async def get_principal_by_id(user_id: str, current_user = Depends(get_current_user)):
    """Get principal data by user ID (admin access)"""
    principal = await get_principal_by_user_id(user_id)
    
    if not principal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Principal not found"
        )
    
    return principal
