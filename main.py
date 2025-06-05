import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

# === Restaurador de identificadores ===
def restaurar_identificadores(resposta: str, mapa_dir: str) -> str:
    substituicoes = {}
    for arquivo in os.listdir(mapa_dir):
        if arquivo.endswith("_mapa.txt"):
            with open(os.path.join(mapa_dir, arquivo), "r", encoding="utf-8") as f:
                for linha in f:
                    if "|" in linha:
                        ident, nome = linha.strip().split("|", 1)
                        substituicoes[ident] = nome

    for ident in sorted(substituicoes, key=len, reverse=True):
        nome = substituicoes[ident]
        resposta = resposta.replace(ident, f"{nome} (identificado como {ident})")

    # Remove mensagem_ok se já houver mensagens de suspeição
    if "<mensagem>" in resposta and "<mensagem_ok>" in resposta:
        import re
        resposta = re.sub(r"<mensagem_ok>.*?</mensagem_ok>", "", resposta, flags=re.DOTALL)

    return resposta

# === INICIALIZAÇÃO ===
load_dotenv()
print('testando...')

# 1. Carrega os arquivos da pasta anonimizados/
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
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    length_function=len,
    separators=["\n\n", "\n", ".", " ", ""]
)
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

# 6. Prompt personalizado
prompt_personalizado = """#PERSONA:
Você é um analista com mais de 30 anos de experiência, especialista em análise de impedimento, suspeição e competência de câmaras em processos jurídicos.

#OBJETIVO:
1. Identificar se há impedimento ou suspeição com base em identificadores anonimizados encontrados no texto.
2. Confirmar se o processo trata de matéria de Direito Público e, portanto, deve tramitar na 3ª Câmara de Direito Público.

#TAREFAS:

### [IMPEDIMENTO E SUSPEIÇÃO]

1. Analise o conteúdo integral do processo.
2. Identifique todos os identificadores `#SUSP_<IDENTIFICADOR>` no texto.
3. Liste cada identificador único apenas uma vez.
4. Para cada identificador listado, retorne a seguinte mensagem:
<mensagem>
*ATENÇÃO!* O processo possui possível impedimento ou suspeição: participante identificado como `#SUSP_<IDENTIFICADOR>`.
</mensagem>
5. Se nenhum identificador `#SUSP_` for encontrado, retorne:
<mensagem_ok>
O processo está livre de impedimentos e suspeições.
</mensagem_ok>

### [COMPETÊNCIA – 3ª CÂMARA DE DIREITO PÚBLICO]

6. Verifique se o processo trata de matéria típica de Direito Público, com base em:
   - Envolvimento de ente público
   - Temas como: servidores públicos, licitações, contratos, improbidade, tributos, atos administrativos
7. Se for Direito Público, retorne:
<mensagem_competencia>
✅ Confirma-se que o processo deve tramitar na **3ª Câmara de Direito Público**.
</mensagem_competencia>
8. Caso contrário, retorne:
<mensagem_competencia_erro>
⚠️ Atenção: o processo não apresenta elementos que justifiquem sua tramitação na 3ª Câmara de Direito Público.
</mensagem_competencia_erro>

### [CONFORMIDADE NORMATIVA]
9. Comente se há indício de irregularidade processual com base no CPC ou Regimento Interno.
"""

# 7. Junta os textos + prompt
conteudo = "\n".join([doc.page_content for doc in texts])
entrada = f"{prompt_personalizado}\n\n{conteudo[:15000]}"  # Limite de segurança

# 8. Envia direto para o modelo
print(f"\n🧠 Enviando análise para o modelo...")
resposta = llm.invoke(entrada)

# 9. Restaura identificadores para nomes reais
resposta_final = restaurar_identificadores(resposta.content, mapa_dir="mapas")

print(f"\n✅ Resposta final:\n{resposta_final}")
