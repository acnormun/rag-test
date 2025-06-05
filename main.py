import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA

# Carrega variáveis de ambiente
load_dotenv()

print('testando...')
# 1. Carrega os arquivos da pasta anonimizados/
from langchain_community.document_loaders import TextLoader

caminho_base = "anonimizados/"
arquivos_txt = [f for f in os.listdir(caminho_base) if f.endswith(".txt")]

if not arquivos_txt:
    print("⚠️ Nenhum arquivo .txt encontrado em 'anonimizados/'.")
    exit()

documents = []
for nome in arquivos_txt:
    try:
        caminho = os.path.join(caminho_base, nome)
        print(f"📥 Lendo: {nome}")
        loader = TextLoader(caminho, encoding='utf-8')
        documents.extend(loader.load())
    except Exception as e:
        print(f"❌ Erro ao carregar {nome}: {e}")

print(f"📄 Documentos carregados: {len(documents)}")

# 2. Divide os documentos
text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
texts = text_splitter.split_documents(documents)
print(f"🧩 Partes (chunks) geradas: {len(texts)}")

if not texts:
    print("⚠️ Nenhum texto carregado. Verifique os arquivos .txt na pasta 'anonimizados/'.")
    exit()

# 3. Gera embeddings
embeddings = OpenAIEmbeddings()

# 4. Cria base vetorial
db = FAISS.from_documents(texts, embeddings)

# 5. Define modelo LLM
llm = ChatOpenAI(model_name="gpt-3.5-turbo")

# 6. Configura sistema RAG com verbose para debug
qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=db.as_retriever(),
    verbose=True  # Mostra o prompt enviado ao LLM
)

# 7. Faz uma pergunta
pergunta = "Qual o número do processo?"
print(f"\n❓ Pergunta: {pergunta}")
resposta = qa.run(pergunta)
print(f"\n✅ Resposta: {resposta}")
