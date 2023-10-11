from pydantic import validator, parse_obj_as
from pydantic.main import BaseModel
from typing import  Any, Dict, List


class RowData(BaseModel):
    text: str

class Hit(BaseModel):
    _id: int
    _row_data: RowData
    _score: float
    _distance: float

class ResponseData(BaseModel):
    hits: List[Hit]

def parse_results(results: List[Dict[str, Any]]) -> ResponseData:
    return parse_obj_as(ResponseData, {"hits": results})

class SearchParamsL2(BaseModel):
    metric_type: str = "L2"
    index_type: str  = "HNSW"
    ef : int = 5 # search scope
    limit : int = 5

    class Config:
        validate_assignment = True  # This enforces strict validation

class QueryL2(BaseModel):
    query: str
    collection_name: str
    search_params: SearchParamsL2  # Include the Se

    class Config:
        validate_assignment = True  # This enforces strict validation

    @validator('query')
    def validate_query_not_empty(cls, value):
        if value is None or len(value.strip()) == 0:
            raise ValueError('query cannot be empty')
        return value

    @validator('collection_name')
    def validate_collection_name_not_empty(cls, value):
        if value is None or len(value.strip()) == 0:
            raise ValueError('collection_name cannot be empty')
        return value


class QueryL2Partition(BaseModel):
    query: str
    collection_name: str
    partition_name: str
    search_params: SearchParamsL2  # Include the Se

    class Config:
        validate_assignment = True  # This enforces strict validation



    @validator('query')
    def validate_query_not_empty(cls, value):
        if value is None or len(value.strip()) == 0:
            raise ValueError('query cannot be empty')
        return value

    @validator('collection_name')
    def validate_collection_name_not_empty(cls, value):
        if value is None or len(value.strip()) == 0:
            raise ValueError('collection_name cannot be empty')
        return value

    @validator('partition_name')
    def validate_partition_name_not_empty(cls, value):
        if value is None or len(value.strip()) == 0:
            raise ValueError('partition_name cannot be empty')
        return value

class SearchParamsIP(BaseModel):
    metric_type: str = "IP"
    index_type: str= "HNSW"
    ef: int = 5  # search scope
    limit: int = 5

    class Config:
        validate_assignment = True  # This enforces strict validation



class QueryIP(BaseModel):
    query: str
    collection_name: str
    search_params: SearchParamsIP  #

    class Config:
        validate_assignment = True  # This enforces strict validation


    @validator('query')
    def validate_query_not_empty(cls, value):
        if value is None or len(value.strip()) == 0:
            raise ValueError('query cannot be empty')
        return value

    @validator('collection_name')
    def validate_collection_name_not_empty(cls, value):
        if value is None or len(value.strip()) == 0:
            raise ValueError('query cannot be empty')
        return value



class QueryIPartition(BaseModel):
    query: str
    collection_name: str
    partition_name: str
    search_params: SearchParamsIP  #

    class Config:
        validate_assignment = True  # This enforces strict validation


    @validator('query')
    def validate_query_not_empty(cls, value):
        if value is None or len(value.strip()) == 0:
            raise ValueError('query cannot be empty')
        return value


    @validator('collection_name')
    def validate_collection_name_not_empty(cls, value):
        if value is None or len(value.strip()) == 0:
            raise ValueError('collection_name cannot be empty')
        return value

    @validator('partition_name')
    def validate_partition_name_not_empty(cls, value):
        if value is None or len(value.strip()) == 0:
            raise ValueError('partition_name cannot be empty')
        return value


class CreatePartition(BaseModel):
    collection_name: str
    partition_name: str

    class Config:
        validate_assignment = True  # This enforces strict validation



class CreateCollection(BaseModel):
    collection_name: str
    partition_name: str
    metric_type : str

    class Config:
        validate_assignment = True  # This enforces strict validation


    @validator('metric_type')
    def validate_metric_type(cls, value):
        print(value)
        if value not in ["IP","L2"]:
            raise ValueError('Metric type is invalid')
        return value


class InsertCollection(BaseModel):
    collection_name: str
    partition_name: str = "Default partition"
    chunk_size : int
    overlap_size : int


class SynthCreateMilvus(BaseModel):
    collection_name: str
    partition_name: str
    synth_id: str
    index_name: str
    urls : List[str]
    overlap_size : int = 500
    chunk_size : int = 1500
    metric_type : str = "IP"


    class Config:
        validate_assignment = True  # This enforces strict validation
    @validator('collection_name')
    def validate_collection_name_not_empty(cls, value):
        if value is None or len(value.strip()) == 0:
            raise ValueError('collection_name cannot be empty')
        return value

    @validator('partition_name')
    def validate_partition_name_not_empty(cls, value):
        if value is None or len(value.strip()) == 0:
            raise ValueError('partition_name cannot be empty')
        return value







