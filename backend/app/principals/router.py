from fastapi import APIRouter, HTTPException, status, Depends
from app.principals.schemas import PrincipalResponse, PrincipalUpdate, PrincipalCreateRequest
from app.principals.crud import get_principal_by_teacher_id, update_principal, create_principal
from app.teachers.crud import get_teacher_by_user_id
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/principals", tags=["principals"])


@router.post("/", response_model=PrincipalResponse, status_code=status.HTTP_201_CREATED)
async def create_my_principal_profile(
    data: PrincipalCreateRequest,
    current_user=Depends(get_current_user)
):
    """
    Create principal profile for the currently logged-in user.
    The user must already have a Teacher profile — Principal links to Teacher.
    """
    teacher = await get_teacher_by_user_id(current_user.id)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must create a Teacher profile before becoming a Principal."
        )

    existing = await get_principal_by_teacher_id(teacher.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Principal profile already exists"
        )

    return await create_principal(
        teacher_id=teacher.id,
        
        experience=data.experience
    )


# @router.get("/me", response_model=PrincipalResponse)
# async def get_my_principal_data(current_user=Depends(get_current_user)):
#     """Get current user's principal data (resolved via teacher record)"""
#     principal = await get_principal_by_user_id(current_user.id)
#     if not principal:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Principal profile not found. Please complete your profile setup."
#         )
#     return principal


@router.put("/me", response_model=PrincipalResponse)
async def update_my_principal_data(
    principal_data: PrincipalUpdate,
    current_user=Depends(get_current_user)
):
    """Update current user's principal data"""
    teacher = await get_teacher_by_user_id(current_user.id)
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher profile not found")

    existing = await get_principal_by_teacher_id(teacher.id)
    if not existing:
        raise HTTPException(status_code=404, detail="Principal profile not found")

    return await update_principal(teacher.id, principal_data)
