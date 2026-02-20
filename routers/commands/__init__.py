__all__ = ("router", )


from aiogram import Router
from .base_commands import router as base_commands_router
from .user_commands import router as user_commands_router
from .estimate_commands import router as estimate_commands_router


router = Router()
router.include_routers(base_commands_router, user_commands_router, estimate_commands_router)
