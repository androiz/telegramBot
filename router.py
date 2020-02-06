from starlette.routing import Route

from views import handler

routes = [
    Route("/", endpoint=handler, methods=['POST'])
]
