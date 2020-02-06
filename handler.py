import uvicorn
from starlette.applications import Starlette

from router import routes


app = Starlette(debug=True, routes=routes)


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000, log_level="debug")
