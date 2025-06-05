import os
import re
import fitz  # PyMuPDF
import unicodedata

# === Normalização segura para comparar ===
def normalizar(texto: str) -> str:
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode().lower().strip()

# === Carrega nomes suspeitos com identificadores ===
def carregar_suspeitos_mapeados(caminho="suspeitos.txt") -> dict:
    mapa = {}
    with open(caminho, "r", encoding="utf-8") as f:
        for linha in f:
            if "|" in linha:
                ident, nome = linha.strip().split("|", 1)
                partes = nome.strip().split()
                # Gera combinações de partes (2 ou mais palavras)
                for i in range(len(partes)):
                    for j in range(i+1, len(partes)+1):
                        trecho = " ".join(partes[i:j])
                        if len(trecho.split()) >= 2:  # Evita palavras únicas
                            chave = normalizar(trecho)
                            mapa[chave] = ident
    return mapa


# === Extrai nomes compostos (até 5 palavras com iniciais maiúsculas) ===
def extrair_nomes(texto):
    padrao_nome = r'\b(?:[A-ZÁ-Ú]{2,}|[A-ZÁ-Ú][a-zá-ú]{2,})(?:\s+(?:[dD][aeo]s?|[Dd]e|[Dd]o|[Dd]a)?\s*(?:[A-ZÁ-Ú]{2,}|[A-ZÁ-Ú][a-zá-ú]{2,})){0,4}\b'
    nomes = re.findall(padrao_nome, texto)

    # Remove duplicatas e palavras comuns não nomeáveis
    palavras_descartadas = {'E', 'EM', 'NO', 'NA', 'DOS', 'DAS', 'DE', 'DO', 'DA', 'AOS', 'AO'}
    nomes_filtrados = [n.strip() for n in set(nomes) if n.upper() not in palavras_descartadas and len(n.strip()) >= 3]

    return nomes_filtrados

# === Aplica regex de anonimização genérica ===
def anonimizar_texto(texto: str) -> str:
    substituicoes = {
        r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b': '[CPF]',
        r'\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b': '[CNPJ]',
        r'\b\d{2}/\d{2}/\d{4}\b': '[DATA]',
        r'\b\d{4}-\d{2}-\d{2}\b': '[DATA_ISO]',
        r'\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b': '[EMAIL]',
        r'\b\d{5}-\d{3}\b': '[CEP]',
        r'\b(?:\(?\d{2}\)?\s?)?(?:9?\d{4})-?\d{4}\b': '[TELEFONE]'
    }
    for padrao, substituto in substituicoes.items():
        texto = re.sub(padrao, substituto, texto)
    return texto

# === Substitui nomes por identificadores e aplica anonimização ===
def anonimizar_com_identificadores(texto: str, mapa_suspeitos: dict) -> tuple[str, dict]:
    nomes_encontrados = extrair_nomes(texto)
    reverso = {}
    contador_nomes = 1  # para nomes genéricos sem suspeição

    for nome in nomes_encontrados:
        nome_norm = normalizar(nome)

        if nome_norm in mapa_suspeitos:
            ident = mapa_suspeitos[nome_norm]
            padrao = re.compile(rf'\b{re.escape(nome)}\b', flags=re.IGNORECASE)
            texto, num_subs = padrao.subn(ident, texto)
            if num_subs > 0:
                reverso[ident] = nome
                print(f"🔐 SUSPEITO detectado: '{nome}' → {ident} ({num_subs}x)")
        else:
            ident = f"#NOME_{contador_nomes:03}"
            padrao = re.compile(rf'\b{re.escape(nome)}\b', flags=re.IGNORECASE)
            texto, num_subs = padrao.subn(ident, texto)
            if num_subs > 0:
                reverso[ident] = nome
                print(f"🔒 Nome comum: '{nome}' → {ident} ({num_subs}x)")
                contador_nomes += 1

    texto_anon = anonimizar_texto(texto)
    return texto_anon, reverso

# === Extrai texto do PDF, anonimiza e salva resultado + mapa ===
def processar_pdf(caminho_pdf: str, saida_txt: str, mapa_suspeitos: dict, saida_mapeamento: str):
    doc = fitz.open(caminho_pdf)
    texto_total = ""
    mapa_reverso = {}

    for pagina in doc:
        texto = pagina.get_text()
        texto_anon, reverso = anonimizar_com_identificadores(texto, mapa_suspeitos)
        texto_total += texto_anon + "\n"
        mapa_reverso.update(reverso)

    with open(saida_txt, "w", encoding="utf-8") as f:
        f.write(texto_total)

    if mapa_reverso:
        with open(saida_mapeamento, "w", encoding="utf-8") as f:
            for ident, nome in mapa_reverso.items():
                f.write(f"{ident}|{nome}\n")

# === Processa todos os PDFs da pasta especificada ===
def processar_pasta(pasta_entrada: str, pasta_saida: str, pasta_mapas: str, mapa_suspeitos: dict):
    os.makedirs(pasta_saida, exist_ok=True)
    os.makedirs(pasta_mapas, exist_ok=True)

    for arquivo in os.listdir(pasta_entrada):
        if arquivo.lower().endswith(".pdf"):
            nome_base = arquivo.replace(".pdf", "")
            caminho_pdf = os.path.join(pasta_entrada, arquivo)
            saida_txt = os.path.join(pasta_saida, f"{nome_base}.txt")
            saida_mapeamento = os.path.join(pasta_mapas, f"{nome_base}_mapa.txt")

            print(f"📄 Processando: {arquivo}")
            processar_pdf(caminho_pdf, saida_txt, mapa_suspeitos, saida_mapeamento)

# === Execução principal ===
if __name__ == "__main__":
    mapa_suspeitos = carregar_suspeitos_mapeados("suspeitos.txt")
    processar_pasta("docs", "anonimizados", "mapas", mapa_suspeitos)
