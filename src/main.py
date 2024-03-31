from fastapi import FastAPI
import uvicorn

import auth.routes
import contacts.routes

contacts_api = FastAPI()

contacts_api.include_router(contacts.routes.router)
contacts_api.include_router(auth.routes.router)



if __name__ == "__main__":
    uvicorn.run(
        "main:contacts_api", host="0.0.0.0", port=8000, reload=True
    )