# from pypdf import PdfReader
# import pymupdf
from fastapi import UploadFile
import io
import os
from llama_cloud_services import LlamaParse
from llama_cloud_services.parse import ResultType
from llama_index.core.bridge.langchain import RecursiveCharacterTextSplitter

from rag_agents import Answer_Generator
from constant import CHUNK_OVERLAP, CHUNK_SIZE
from embedding import embed_text, embed_text_with_fastEmbed, embed_texts
from qdrant import add_documents, search_document_chunks

# from langchain_community.document_loaders import PyMuPDFLoader

# def read_file_using_pypdf(file):
# reader = PdfReader(file)

# # Extract text from all pages
# raw_text = ""
# for page_num, page in enumerate(reader.pages):
#     page_text = page.extract_text()
#     raw_text += page_text

# return (raw_text)

# def read_file_using_pymupdf(file: UploadFile):
# Read the file content from UploadFile
# file_content = file.file.read()

# # Create a BytesIO object from the content

# file_stream = io.BytesIO(file_content)

# # Open the document using PyMuPDF
# doc = pymupdf.open(stream=file_stream, filetype="pdf")

# raw_text = ""
# for page in doc: # iterate the document pages
#     text = page.get_text() # get plain text (already in UTF-8)
#     raw_text += text # write text of page

# doc.close()

# return raw_text


# def read_file_using_pymupdf_langchain(file: UploadFile):
# Read the file content from UploadFile
# file_content = file.file.read()

# # Create a BytesIO object from the content

# file_stream = io.BytesIO(file_content)

# # Open the document using PyMuPDF
# loader = PyMuPDFLoader(stream=file_stream, filetype="pdf")

# doc = loader.load()

# raw_text = ""
# for page in doc: # iterate the document pages
#     text = page.get_text() # get plain text (already in UTF-8)
#     raw_text += text # write text of page

# doc.close()

# return raw_text


def read_file(file: UploadFile):
    #  Read the file content from UploadFile
    file_content = file.file.read()

    # Create a BytesIO object from the content

    file_stream = io.BytesIO(file_content)

    parser = LlamaParse(
        api_key=os.getenv(
            "LLAMA_CLOUD_API_KEY"
        ),  # can also be set in your env as LLAMA_CLOUD_API_KEY
        num_workers=4,  # if multiple files passed, split in `num_workers` API calls
        verbose=True,
        language="en",
        result_type=ResultType.MD,  # optionally define a language, default=en
    )

    # Pass the file stream to the parse method with file name in extra_info
    parsed_text = parser.parse(
        file_path=file_stream, extra_info={"file_name": file.filename}
    )

    raw_text = ""

    for page in parsed_text.pages:
        raw_text += page.md

    chunks = create_chunks(raw_text)

    # embeddings = embed_text_with_fastEmbed(chunks)

    add_documents(chunks)

    return {
        "pages": len(parsed_text.pages),
        "content_chars": len(raw_text),
        "chunks": len(chunks),
    
    }


def create_chunks(raw_text: str):
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    ).split_text(raw_text)

    return chunks


def query_document(query: str):
    search_results = search_document_chunks(query)
    print("SEARCH RESULTS", len(search_results))
    relevant_chunk = [result.document for result in search_results]
    for chunk in search_results:
        print("CHUNK", chunk.score)
    relevant_chunk_text = "\n".join(relevant_chunk)
    

    answer = Answer_Generator(query, relevant_chunk_text)

    return answer