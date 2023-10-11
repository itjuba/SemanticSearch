import csv
from io import BytesIO
import openai
import requests
from PyPDF2.errors import PdfReadError
from fastapi import HTTPException
from langchain.text_splitter import RecursiveCharacterTextSplitter
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_not_exception_type
from PyPDF2 import PdfReader
import tiktoken
from pymilvus import Partition,Collection,CollectionSchema, FieldSchema, DataType
import os

openai.api_key =  os.environ["OPENAI_API_KEY"]
EMBEDDING_MODEL = 'text-embedding-ada-002'
EMBEDDING_CTX_LENGTH = 8191
EMBEDDING_ENCODING = 'cl100k_base'

def is_scrapable(url):
    try:
        response = requests.get(url)
        print(response.headers,response.content)
        if response.status_code == 200:
            content_type = response.headers.get('content-type')
            print("content type",content_type)
            if content_type and 'text/html' in content_type:
                return True
    except requests.RequestException:
        pass
    return False

async def get_document_schema(metric_type):
    pk = FieldSchema(
        name="pk",
        dtype=DataType.INT64,
        is_primary=True,
        auto_id=True,
    )

    text = FieldSchema(
        name="text",
        dtype=DataType.VARCHAR,
        max_length=65535
    )

    vector = FieldSchema(
        name="vector",
        dtype=DataType.FLOAT_VECTOR,
        dim=1536
    )

    schema = CollectionSchema(
        fields=[pk, text, vector],
        description="document_upload"
    )

    index_params = {
        "metric_type": metric_type,
        "index_type": "HNSW",
        "params": {"M": 8, "efConstruction": 64}
    }

    return schema,index_params


async def get_document_schema_qa(metric_type):
    pk = FieldSchema(
        name="pk",
        dtype=DataType.INT64,
        is_primary=True,
        auto_id=True,
    )

    answer = FieldSchema(
        name="text",
        dtype=DataType.VARCHAR,
        max_length=65535
    )

    question_vector = FieldSchema(
        name="vector",
        dtype=DataType.FLOAT_VECTOR,
        dim=1536
    )

    schema = CollectionSchema(
        fields=[pk, question_vector, answer],
        description="document_upload"
    )

    index_params = {
        "metric_type": metric_type,
        "index_type": "HNSW",
        "params": {"M": 8, "efConstruction": 64}
    }

    return schema,index_params

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6),retry=retry_if_not_exception_type(openai.InvalidRequestError))
def get_embedding(text, model="text-embedding-ada-002"):
   # text = text.replace("\n", " ")
   return openai.Embedding.create(input = [text], model=model)['data'][0]['embedding']


def detect_csv_delimiter(filename):
    with open(filename, 'r', encoding='utf-8') as csv_file:
        sample = csv_file.read(1024)  # Read a small sample of the file to detect delimiter
        dialect = csv.Sniffer().sniff(sample)
        return dialect



# need for review
def validate_collection_and_parition(collection_name,partition_name):

    collection = Collection(collection_name)
    if not collection.has_partition(partition_name):
        raise HTTPException(status_code=400, detail="Collection or partition parameter is invalid")

    return collection

#############"
def is_valid_pdf_file(file_path):
    _, file_extension = os.path.splitext(file_path)
    if  file_extension.lower() != '.pdf':
        return HTTPException(status_code=400, detail="Invalid file")


def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def embed_qa(file_path, partition_name, collection_name,dialect):
    question_embeddings = []
    answers = []
    with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile,dialect=dialect)
        headers = next(reader)  # Read the first row as headers

        print("headers",headers,dialect)
        if len(headers) != 2:
            raise ValueError("Invalid file format. csv file should contain 2 columns only 'answers' and 'questions' ")

        if headers[0].strip().lower() != 'questions' or headers[1].strip().lower() != 'answers':
            raise ValueError("Invalid file format. csv file should contain 2 columns named 'answers' and 'questions'")


        for row in reader:
            if row[0] == "" or row[1]=="":
                raise ValueError("Empty columns error")

            question_embedding = get_embedding(row[0])
            question_embeddings.append(question_embedding)
            answers.append(row[1])

    data = [
        question_embeddings,
        answers,
    ]

    if data[0] == [] or data[1]==[]:
        raise ValueError("Invalid file. empty file")

    partition = Partition(name=partition_name, collection=collection_name)
    partition.insert(data)
    partition.flush()

    return "QA data uploaded"



def embed_scraped_data(synth_scraped_data,collection_name,partition_name):
    vectors = []
    texts = []


    for row in synth_scraped_data:
        question_embedding = get_embedding(row.page_content)
        vectors.append(question_embedding)
        texts.append(row.page_content)

    data = [
        texts,
        vectors,
    ]

    print(data)
    if data[0] == [] or data[1]==[]:
        raise ValueError("Invalid file. empty data")

    partition = Partition(name=partition_name, collection=collection_name)
    partition.insert(data)
    partition.flush()

    return "website data uploaded"


def embedd_pdf(chunk_size,chunk_overlap,file_path,partition_name,collection_name):

    pdf_re = PdfReader(file_path)
    paragraphs = []


    for i in range(len(pdf_re.pages)):
        page = pdf_re.pages[i]
        page_text = "".join(page.extract_text())
        paragraphs.extend(page_text.split('\n'))


    text_ = " ".join(paragraphs)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap) # splited text with chunk_size/chunk_overlap
    chunked_text = text_splitter.split_text(text_)

    text_embed_list = []
    data_text = []



    if chunked_text==[]:
        raise HTTPException(status_code=400, detail="Invalid pdf file")

    for text in chunked_text:
        data_embedding = get_embedding(text)
        data_text.append(str(text))
        text_embed_list.append(data_embedding)



    data = [
        data_text,
        text_embed_list,
    ]

    partition = Partition(name=partition_name, collection=collection_name)
    partition.insert(data)
    partition.flush()

    return "document uploaded"


def has_text_content_from_bytes(pdf_content):
    # Create a file-like object from the PDF content
    pdf_file = BytesIO(pdf_content)

    # Create a PDF reader object
    pdf_reader = PdfReader(pdf_file)

    # Loop through each page of the PDF
    for page_number in range(len(pdf_reader.pages)):
        # Get the page object
        page = pdf_reader.pages[page_number]

        # Try to extract text from the page
        page_text = page.extract_text()

        # Check if the extracted text is not empty
        if page_text.strip():
            return True

    # If no text is found in any page, return False
    return False


async def validate_pdf_files(files):
    for file in files:
        try:
            # Read the contents of the uploaded file as bytes
            file_content =  await file.read()
            pdf_has_text_ = has_text_content_from_bytes(file_content)
            if pdf_has_text_==False:
                raise HTTPException(status_code=400, detail="Invalid pdf file, no text data")

            # Try to create a PdfReader object to validate the file as a PDF
            PdfReader(file_content)
            # Do whatever you want to do with valid PDF files here
            # For example, you could save them to disk or process them further
        except PdfReadError:
            raise HTTPException(status_code=400, detail="Invalid pdf file")



def validate_csv_file(file):
    try:
        # Check if the file has a valid CSV extension
        print(file.filename)
        if not file.filename.lower().endswith('.csv'):
                raise ValueError("Invalid file format. Only CSV files are allowed.")


        return True

    except Exception as e:
        raise ValueError("Invalid CSV file: " + str(e))


def validate_collection_and_partition(collection_name,partition_name):
    collection = Collection(collection_name)
    if not collection.has_partition(partition_name):
        raise HTTPException(status_code=400, detail="Collection or partition parameter is invalid")

    return collection
