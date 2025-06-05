import os
import re
import fitz  # PyMuPDF

def anonimizar_texto(texto: str) -> str:
    substituicoes = {
        r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b': '[CPF]',
        r'\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b': '[CNPJ]',
        r'\b\d{2}/\d{2}/\d{4}\b': '[DATA]',
        r'\b\d{4}-\d{2}-\d{2}\b': '[DATA_ISO]',
        r'\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b': '[EMAIL]',
        r'\b\d{5}-\d{3}\b': '[CEP]',
        r'\b(?:\(?\d{2}\)?\s?)?(?:9?\d{4})-?\d{4}\b': '[TELEFONE]',
        r'\b(?:Sr\\.?|Sra\\.?|Dr\\.?|Dra\\.?|Excelent[íssim][ao])\\s+[A-ZÁ-ÚÂ-Û][a-zá-úâ-û]+(?:\\s+[A-ZÁ-ÚÂ-Û][a-zá-úâ-û]+)*\b': '[NOME]',
        r'\b[A-ZÁ-ÚÂ-Û][a-zá-úâ-û]+(?:\s+[A-ZÁ-ÚÂ-Û][a-zá-úâ-û]+)+\b': '[POSSIVEL_NOME]'
    }
    for padrao, substituto in substituicoes.items():
        texto = re.sub(padrao, substituto, texto)
    return texto

def processar_pdf(caminho_pdf: str, saida_txt: str):
    doc = fitz.open(caminho_pdf)
    texto_total = ""
    for pagina in doc:
        texto = pagina.get_text()
        texto_anon = anonimizar_texto(texto)
        texto_total += texto_anon + "\n"
    with open(saida_txt, "w", encoding="utf-8") as f:
        f.write(texto_total)

def processar_pasta(pasta_entrada: str, pasta_saida: str):
    os.makedirs(pasta_saida, exist_ok=True)
    for arquivo in os.listdir(pasta_entrada):
        if arquivo.lower().endswith(".pdf"):
            caminho_pdf = os.path.join(pasta_entrada, arquivo)
            saida_txt = os.path.join(pasta_saida, arquivo.replace(".pdf", ".txt"))
            print(f"Processando: {arquivo}")
            processar_pdf(caminho_pdf, saida_txt)

# Uso
if __name__ == "__main__":
    processar_pasta("docs", "anonimizados")
