# Imagem única para os PRJ-01..PRJ-08 e o portal.
#
# O código NÃO é copiado: o docker-compose monta a raiz do monorepo em /app.
# Assim uma edição no host vale na hora, sem rebuild — que é o que se quer
# num ambiente de desenvolvimento.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# build-essential é exigido por chromadb/sentence-transformers na instalação.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# O contexto de build é esta pasta (docker/), não a raiz do monorepo.
# Motivo: a raiz tem 13 GB e ~160 mil arquivos; mandar tudo para o daemon
# fazia o build travar antes mesmo de começar a instalar qualquer coisa.
# A imagem não precisa do código — ele chega por volume no compose.
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# FastAPI e Streamlit; a porta real de cada serviço vem do compose.
EXPOSE 8000
EXPOSE 8501

CMD ["bash"]
