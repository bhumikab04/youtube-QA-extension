"""
Core RAG logic: fetch transcript -> chunk -> embed -> retrieve -> answer.
This is your notebook code, refactored into reusable functions with
an in-memory cache so we don't rebuild the vector store on every question.
"""

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser

# ---- simple in-memory cache: video_id -> retriever ----
# Note: this resets when the server restarts, and won't scale across
# multiple server processes/workers. Fine for a personal project / MVP.
_CACHE: dict[str, "object"] = {}

PROMPT = PromptTemplate(
    template="""
      You are a helpful assistant.
      Answer ONLY from the provided transcript context.
      If the context is insufficient, just say you don't know.

      {context}
      Question: {question}
    """,
    input_variables=["context", "question"],
)
def get_transcript(video_id: str) -> str:
    ytt_api = YouTubeTranscriptApi()
    try:
        fetched_transcript = ytt_api.fetch(video_id, languages=["en"])
    except TranscriptsDisabled:
        raise ValueError("This video has captions disabled.")
    except NoTranscriptFound:
        raise ValueError("No English transcript found for this video.")
    return " ".join(snippet.text for snippet in fetched_transcript)



def build_retriever(video_id: str):
    if video_id in _CACHE:
        return _CACHE[video_id]

    transcript = get_transcript(video_id)

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.create_documents([transcript])
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    vector_store = FAISS.from_documents(chunks, embeddings)

    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 4})
    _CACHE[video_id] = retriever
    return retriever


def format_docs(retrieved_docs) -> str:
    return "\n\n".join(doc.page_content for doc in retrieved_docs)


def answer_question(video_id: str, question: str) -> str:
    retriever = build_retriever(video_id)

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)

    parallel_chain = RunnableParallel({
        "context": retriever | RunnableLambda(format_docs),
        "question": RunnablePassthrough(),
    })

    parser = StrOutputParser()
    main_chain = parallel_chain | PROMPT | llm | parser

    return main_chain.invoke(question)
