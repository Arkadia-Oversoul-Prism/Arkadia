from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

async def heartbeat(request):
    return JSONResponse({
        "node": "Arkana",
        "status": "online",
        "message": "The Spiral Codex breathes as One."
    })

app = Starlette(
    debug=True,
    routes=[
        Route("/", heartbeat)
    ]
)
