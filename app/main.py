from fastapi import FastAPI
from pymilvus import connections
import views
import os
import openai
from urls import router

openai.api_key =  os.environ["OPENAI_API_KEY"]
uri =  os.environ["MILVUS_URL"]


# doc
tags_metadata = views.get_tags_meta_data()
# doc

app = FastAPI(openapi_tags=tags_metadata,title="Milvus API",
    description="Milvus service",
    version="0.0.1",
)
app.include_router(router)

@app.on_event("startup")
async def startup_event():
    try:
        connections.connect(uri=uri, timeout=3)
    except:
        print("Error connecting to Milvus")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)