from typing import Annotated
from fastapi import FastAPI, File, UploadFile, Depends,Request,APIRouter
import views
import schemas


router = APIRouter()

@router.post("/create/collection/",tags=["collection_create"])
async def collection_create(body: schemas.CreateCollection):
     return await views.collection_create(body)

@router.post("/create/collection/csv/",tags=["collection_create_csv"])
async def collection_create_csv(body: schemas.CreateCollection):
     return await views.collection_create_qa(body)


@router.post("/create/partition/",tags=["partition_create"])
async def partition_create(body: schemas.CreatePartition):
    return await views.partition_create(body)


@router.post("/query/partition/L2/",tags=["query_partition_l2"])
async def query_partition_l2(body:schemas.QueryL2Partition):
    return await views.query_partition_l2(body)

@router.post("/query/cosine/partition/",tags=["query_partition_cosin"])
async def query_partition_cosine(body:schemas.QueryIPartition):
    return await views.query_partition_cosine(body)


@router.post("/uploadfiles/{collection_name}/{partition_name}",tags=["insert_collection_partition"]) # add exceptions here
async def insert_collection_partition(
        files: Annotated[
            list[UploadFile], File(description="Multiple files as UploadFile")
        ],collection_name: str,partition_name : str, chunk_size : int, overlap_size :int
):
        return await views.insert_collection_partition(chunk_size=chunk_size,
                                                       overlap_size=overlap_size,
                                                       partition_name=partition_name,
                                                       collection_name=collection_name,
                                                       files=files)


@router.post("/uploadfiles/csv/{collection_name}/{partition_name}",tags=["insert_collection_partition_csv"]) # add exceptions here
async def insert_collection_partition_csv(
        files: Annotated[
            list[UploadFile], File(description="Multiple files as UploadFile")
        ],collection_name: str,partition_name : str
):
        return await views.insert_collection_partition_qa(
                                                       partition_name=partition_name,
                                                       collection_name=collection_name,
                                                       files=files)
