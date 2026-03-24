from app.core.database import prisma
from app.principals.schemas import PrincipalCreate, PrincipalUpdate

async def get_principal_by_user_id(user_id: str):
    """Get principal by user ID with user data"""
    return await prisma.principal.find_unique(
        where={"userId": user_id},
        include={"user": True}
    )

async def create_principal(principal_data: PrincipalCreate):
    """Create principal record"""
    return await prisma.principal.create(data=principal_data.model_dump())

async def update_principal(user_id: str, principal_data: PrincipalUpdate):
    """Update principal record and associated user data"""
    update_dict = principal_data.model_dump(exclude_unset=True)
    
    # Extract user data if present
    user_data = update_dict.pop("user", None)
    
    # Update user data if provided
    if user_data:
        await prisma.user.update(
            where={"id": user_id},
            data=user_data
        )
    
    # Update principal data if any principal-specific fields are provided
    if update_dict:
        await prisma.principal.update(
            where={"userId": user_id},
            data=update_dict
        )
    
    # Return updated principal with user data
    return await get_principal_by_user_id(user_id)

async def delete_principal(user_id: str):
    """Delete principal record"""
    return await prisma.principal.delete(where={"userId": user_id})
