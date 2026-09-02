from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas import DeviceOut, DeviceUpdate
from app.storage.repository import list_devices, update_device

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("", response_model=list[DeviceOut])
async def get_devices(session: AsyncSession = Depends(get_session)):
    devices = await list_devices(session)
    return [DeviceOut.model_validate({**d.__dict__, "id": str(d.id)}) for d in devices]


@router.patch("/{device_id}", response_model=DeviceOut)
async def patch_device(device_id: str, patch: DeviceUpdate, session: AsyncSession = Depends(get_session)):
    """Manually fill vendor/model/version/name — syslog traffic alone
    doesn't tell us what hardware sent it."""
    device = await update_device(session, device_id, patch)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return DeviceOut.model_validate({**device.__dict__, "id": str(device.id)})
