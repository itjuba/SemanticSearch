from PyPDF2.errors import PdfReadError
from fastapi import HTTPException
from langchain.embeddings import OpenAIEmbeddings
from pymilvus import Partition, Collection, MilvusException
import utils as api_milvus_utils
from pymilvus.exceptions import PartitionNotExistException, SchemaNotReadyException,CollectionNotExistException
from pymilvus import utility
import os

embeddings = OpenAIEmbeddings(embedding_ctx_length=1536)
save_path = "/app/pdf_files_upload/"  # Specify the desired save path
dev=os.getenv("FASTAPI_DEV")
if dev:
    save_path = "./pdf_files_upload/"  # Specify the desired save path


async def collection_create(body):
    try:
        if utility.has_collection(body.collection_name):
            return HTTPException(status_code=400, detail="Collection already exists")

        schema, index_params = await api_milvus_utils.get_document_schema(body.metric_type)
        collection_create = Collection(name=body.collection_name, schema=schema, index_param=index_params,consistency_level="Strong")
        collection_create.create_index("vector", index_params)
        collection_create.create_partition(body.partition_name)

        return {"status_code": 200, "detail": "collection created"}


    except MilvusException:
        raise HTTPException(status_code=400, detail="MilvusException")


async def collection_create_qa(body):
    try:
        if utility.has_collection(body.collection_name):
            return HTTPException(status_code=400, detail="Collection already exists")

        schema, index_params = await api_milvus_utils.get_document_schema_qa(body.metric_type)
        collection_create = Collection(name=body.collection_name, schema=schema, index_param=index_params,
                                       consistency_level="Strong")
        collection_create.create_index("vector", index_params)
        collection_create.create_partition(body.partition_name)

        return {"status_code": 200, "detail": "collection created"}


    except MilvusException:
        raise HTTPException(status_code=400, detail="MilvusException")



async def partition_create(body):
    try:
        if not utility.has_collection(body.collection_name):
            return HTTPException(status_code=400, detail="Collection not found")

        collection = Collection(body.collection_name)  # Get an existing collection.
        if collection.has_partition(body.partition_name):
            return HTTPException(status_code=400, detail="Partition already exists")

        Partition(collection=body.collection_name, name=body.partition_name)
        return {"status_code": 200, "detail": "partition created"}

    except MilvusException:
        raise HTTPException(status_code=400, detail="MilvusException")

async def query_partition_l2(body):
    try:
        if not utility.has_collection(body.collection_name):
            return HTTPException(status_code=400, detail="Collection not found")

        collection = Collection(name=body.collection_name)
        collection.release()

        if not collection.has_partition(partition_name=body.partition_name):
            raise HTTPException(status_code=400, detail="Partition doesn't exists")

        request_embed = embeddings.embed_query(body.query)
        partition = Partition(name=body.partition_name,collection=body.collection_name)
        collection.release()
        partition.load()
        results = partition.search(limit=body.search_params.limit,data=[request_embed],anns_field="vector",
                                    output_fields=["text"],
                                    param={"index_type" : body.search_params.index_type,
                                    "metric_type":body.search_params.metric_type,
                                           "params" : {"ef":body.search_params.ef}})

        data= []
        for hits in results:
            for hit in hits:
                data.append(hit)
        return data


    except PartitionNotExistException:
        raise HTTPException(status_code=400, detail="PartitionNotExistException")

    except SchemaNotReadyException:
        raise HTTPException(status_code=400, detail="Collection doesn't exists")

    except MilvusException:
        raise HTTPException(status_code=400, detail="MilvusException")

async def query_partition_cosine(body):
    try:
        # search_params = {"metric_type": "IP", "index_type": "HNSW", "params": {"nprobe": 5 ,"M":8 , "efConstruction" : 64 }}
        if not utility.has_collection(body.collection_name):
            return HTTPException(status_code=400, detail="Collection not found")

        collection = Collection(name=body.collection_name)

        if not collection.has_partition(partition_name=body.partition_name):
            raise HTTPException(status_code=400, detail="Partition doesn't exists")



        partition = Partition(name=body.partition_name, collection=body.collection_name)
        collection.release()
        partition.load()
        request_embed = embeddings.embed_query(body.query)
        results = partition.search(limit=body.search_params.limit, data=[request_embed], anns_field="vector",
                                   output_fields=["text"], param={"index_type": body.search_params.index_type,
                                                                  "metric_type": body.search_params.metric_type,
                                                                  "params": {"ef": body.search_params.ef}})

        data = []
        for hits in results:
            for hit in hits:
                data.append(hit)
        return data

    except PartitionNotExistException:
        raise HTTPException(status_code=400, detail="PartitionNotExistException")

    except SchemaNotReadyException:
        raise HTTPException(status_code=400, detail="Collection doesn't exists")

    except MilvusException:
        raise HTTPException(status_code=400, detail="MilvusException")

async def insert_collection_partition(chunk_size,overlap_size,collection_name,partition_name,files):
    try:
        api_milvus_utils.validate_collection_and_parition(collection_name, partition_name)  # validate collection and partition

        for file in files:
            api_milvus_utils.is_valid_pdf_file(file.filename)

        for file in files:
            # save_path = "/app/pdf_files_upload/"  # Specify the desired save path
            # Create the complete save path by joining the desired path and the filename
            file_path = os.path.join(save_path, file.filename)

            # Open a file in write mode
            with open(file_path, "wb") as f:
                # Read the contents of the uploaded file
                file_contents = await file.read()
                f.write(file_contents)

            api_milvus_utils.embedd_pdf(chunk_size, overlap_size, file_path, partition_name,
                       collection_name)  # upload & insert data into partition
        return {"message": "Files uploaded successfully", "filenames": [file.filename for file in files]}


    except PdfReadError:
        return HTTPException(status_code=400, detail="Invalid pdf file")

    except:
        raise HTTPException(status_code=400, detail="Bad request")



async def insert_collection_partition_qa(collection_name, partition_name, files):
    try:
        api_milvus_utils.validate_collection_and_partition(collection_name, partition_name)

        for file in files:
            api_milvus_utils.validate_csv_file(file)  # Validate the CSV file

        for file in files:
            file_path = os.path.join(save_path, file.filename)

            with open(file_path, "wb") as f:
                file_contents = await file.read()
                f.write(file_contents)

            delimiter = api_milvus_utils.detect_csv_delimiter(file_path)

            api_milvus_utils.embed_qa(file_path, partition_name, collection_name,delimiter)

        return {"message": "Files uploaded successfully", "filenames": [file.filename for file in files]}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def get_tags_meta_data():
    return  [
                {
                    "name": "collection_create",
                    "description": "create a collection with a specific metric IP or L2",
                },
                {
                    "name": "collection_create_csv",
                    "description": "create a collection for csv files with a specific metric IP or L2",
                },

                {
                    "name": "partition_create",
                    "description": "create a partition within a collection",
                } ,
                {
                    "name": "query_partition_l2",
                    "description": "Query a partition using L2 metric, the collection schema should be adequate to the metric search parameters",
                },
               {
                    "name": "query_partition_cosin",
                    "description": "Query a partition using IP (cosin) metric, the collection schema should be adequate to the metric search parameters",
               },
               {
                    "name": "insert_collection_partition",
                    "description": "Upload pdf files into a specific partition",
                },
                {
                    "name": "insert_collection_partition_csv",
                    "description": "Uploading CSV into a partition. The CSV file should contain only 2 columns:  'questions' as column 1 & 'answers' as column 2 strictly",
                },

    {
                    "name": "insert_scrap_data",
                    "description": "Under testing/Uploading scraped data from the provided links to milvus",
                },
            ]


async def insert_scrap_data(body):
    from langchain.document_loaders import UnstructuredURLLoader
    from langchain.text_splitter import CharacterTextSplitter


    try:
        for url in body.urls:
            if api_milvus_utils.is_scrapable(url):
                print(f"{url} is scrapable")
            else:
                print(f"{url} is not scrapable")
                raise ValueError(f"{url} url is not scrapable")

        if utility.has_collection(body.collection_name):
            return HTTPException(status_code=400, detail="Collection already exists")
        await collection_create(body)


        ahmed_loader = UnstructuredURLLoader(urls=body.urls)
        ahmed_data = ahmed_loader.load()
        text_splitter = CharacterTextSplitter(chunk_size=body.chunk_size, chunk_overlap=body.overlap_size)
        synth_docs = text_splitter.split_documents(ahmed_data)

        api_milvus_utils.embed_scraped_data(synth_docs,partition_name=body.partition_name,collection_name=body.collection_name)
        return {"message": "data uploaded successfully", "urls": [url for url in body.urls]}


    except CollectionNotExistException:
        raise HTTPException(status_code=400, detail="PartitionNotExistException")

    except PartitionNotExistException:
        raise HTTPException(status_code=400, detail="PartitionNotExistException")

    except SchemaNotReadyException:
        raise HTTPException(status_code=400, detail="Collection doesn't exists")

    except MilvusException:
        raise HTTPException(status_code=400, detail="MilvusException")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))






