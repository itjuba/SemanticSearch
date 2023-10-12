SemanticSearch using Milvus and HNSW Indexing 
Overview

This project sets up a Semantic Search system using a combination of technologies, including Milvus as the vector database and HNSW indexing for efficient vector search. Below, we delve into the technical details of each component and how they work together.
Components


Milvus

Milvus is the core vector database responsible for efficient storage and retrieval of high-dimensional vectors. It provides support for various similarity search operations using HNSW indexing.

    Container Name: milvus-standalone
    Ports: 19530 (Milvus API) and 9091 (Milvus web interface)
    Depends On: ETCD and Minio
    Function: Milvus acts as the storage engine for vectors and serves as the foundation for similarity searches. It supports HNSW indexing for efficient retrieval.

Attu

Attu is a service that connects your application to the Milvus database. It serves as an interface for your application to interact with the vector search capabilities of Milvus.

    Container Name: attu
    Port: 3000
    Depends On: Milvus
    Function: Attu facilitates communication between your application and Milvus, enabling vector search operations, and serving as a bridge between the two.

Web API

The Web API represents your application, offering an interface for users to interact with the Semantic Search system. It uses the services provided by Milvus and Attu to perform vector searches and retrieve similar vectors.

    Container Name: web_api
    Port: 8000
    Volumes: For application code and uploaded files
    Depends On: ETCD, Minio, Milvus, and Attu
    Function: The Web API exposes endpoints for user interaction, processing search queries, and facilitating vector searches using Milvus.

Nginx

Nginx acts as a reverse proxy server, routing incoming requests to the appropriate services within the system, including the Web API and other components.

    Container Name: milvus-nginx
    Port: 80
    Volumes: For Nginx configuration
    Function: Nginx plays a key role in managing incoming web traffic and directing it to the relevant components of the Semantic Search system.

Customization and Extensibility

This system provides a foundation for Semantic Search but can be customized and extended to meet specific requirements. You have the flexibility to modify Docker Compose configurations, adjust environment variables, and introduce additional services as needed to enhance functionality or scale the system.
