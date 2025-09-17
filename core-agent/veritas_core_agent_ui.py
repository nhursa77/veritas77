import streamlit as st
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain.schema import Document
from core_prompt import SYSTEM_PROMPT
import os

# 🔹 Postavke stranice
st.set_page_config(page_title="Veritas H.77 — CORE", page_icon="⚖️", layout="wide")

st.title("⚖️ Veritas H.77 — CORE (Ustav + UN instrumenti)")

# 🔹 Sidebar
st.sidebar.header("Postavke")
temperature = st.sidebar.slider("Temperatura (kreativnost)", 0.0, 1.0, 0.2, 0.05)
k = st.sidebar.slider("Kontekst segmenata (k)", 2, 12, 6, 1)
chunk_size = st.sidebar.slider("Chunk size (znakovi)", 500, 1500, 800, 50)
overlap = st.sidebar.slider("Overlap (znakovi)", 50, 200, 100, 10)

st.sidebar.markdown("### 📂 Dokumenti učitani u CORE:")
st.sidebar.markdown("- Ustav Republike Hrvatske (`ustav.json`)")
st.sidebar.markdown("- Opća deklaracija o ljudskim pravima (`udhr.json`)")
st.sidebar.markdown("- Međunarodni pakt o građanskim i političkim pravima (`iccpr.json`)")
st.sidebar.markdown("- Međunarodni pakt o gospodarskim, socijalnim i kulturnim pravima (`icescr.json`)")
st.sidebar.markdown("---")
st.sidebar.caption("Identitet i ovlasti definirani su kroz Charter + Identity akte.")

# 🔹 Učitaj Chroma vektorsku bazu
persist_dir = os.path.join("core-agent", "core-indexes", f"chroma_core_agent_{chunk_size}_{overlap}_g5")
embeddings = OllamaEmbeddings(model="mistral")
vectordb = Chroma(persist_directory=persist_dir, embedding_function=embeddings)

# 🔹 Chat povijest
if "messages" not in st.session_state:
    st.session_state.messages = []

# 🔹 Prikaz povijesti
for msg in st.session_state.messages:
    role = "🧑‍💼 Korisnik" if msg["role"] == "user" else "🤖 Veritas H.77"
    with st.chat_message(msg["role"]):
        st.markdown(f"**{role}:** {msg['content']}")

# 🔹 Unos korisnika
if prompt := st.chat_input("Postavi pitanje..."):
    # Dodaj korisnikovu poruku u povijest
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(f"**🧑‍💼 Korisnik:** {prompt}")

    # Pretraži dokumente
    docs = vectordb.similarity_search(prompt, k=k)

    # Spoji sadržaj dokumenata
    context = "\n\n".join([f"[{d.metadata.get('doc_id', 'NEPOZNATO')} čl.{d.metadata.get('article', '?')}]\n{d.page_content}" for d in docs])

    # Prompt za agenta
    full_prompt = f"""{SYSTEM_PROMPT}

Korisničko pitanje:
{prompt}

Relevantni izvodi:
{context}

Odgovori isključivo citiranjem iz gornjih izvoda.
"""

    # 🧠 Pozovi Ollama model
    import ollama
    response = ollama.chat(model="mistral", messages=[{"role": "system", "content": SYSTEM_PROMPT},
                                                     {"role": "user", "content": full_prompt}])

    answer = response["message"]["content"]

    # Dodaj odgovor u povijest
    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(f"**🤖 Veritas H.77:** {answer}")
