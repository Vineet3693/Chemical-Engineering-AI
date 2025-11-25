# <span style="color:#0072B1">🧪 Chemical Engineering RAG System</span>

_Discover answers in seconds: built for students, researchers, and pros_

---

## <span style="color:#028A0F">✨ Features</span>
- **📚 Book-Based Q&A:** Semantic search from 4-5 textbooks  
- **🌐 General Knowledge Mode:** Tap into Gemini's AI knowledge  
- **💾 Persistent Storage:** ChromaDB with auto-save  
- **📥 Export:** Download answers as PDF or DOCX  
- **📖 Citations:** Automatic book/page referencing  
- **💬 Chat History:** View and export queries  
- **🎨 Modern UI:** Intuitive dashboard with stylish design

---

## <span style="color:#FF9800">🚀 Quick Start</span>
<details>
<summary><strong>Show Steps</strong></summary>

1. Install <span style="color:#4A90E2;">Python 3.8+</span>  
2. Get your <span style="color:#FFD700;">Google Gemini API key</span> ([How?](https://makersuite.google.com/app/apikey))  
3. Place your textbooks in <code>data/books/</code>  
4. Install dependencies  
   <pre><code>pip install -r requirements.txt</code></pre>
5. Configure <code>.env</code> with your API key  
6. Launch the app  
   <pre><code>streamlit run app.py</code></pre>
7. Open your browser: <span style="color:#C71585;">http://localhost:8501</span>
</details>

---

## <span style="color:#AB47BC">📚 Tech Stack</span>
| Component         | Technology            |
| ----------------- | -------------------- |
| **UI Framework**  | Streamlit            |
| **Vector DB**     | ChromaDB             |
| **LLM**           | Google 2.5 Flash    |
| **Embeddings**    | sentence-transformers|
| **PDF Handling**  | PyMuPDF (fitz)       |
| **Export**        | ReportLab, python-docx|

---

## <span style="color:#00BFAE">💡 Example Queries</span>
- What are the different types of heat exchangers?
- Explain the Haber process for ammonia synthesis
- Advances in green chemistry?
- How is AI used in chemical engineering?

---

## <span style="color:#E57373">🛠️ Troubleshooting</span>
- **PDFs not found:** Check <code>data/books/</code>  
- **API key issues:** Verify <code>.env</code>  
- **RAG errors:** Check requirements & Python 3.8+  
- **Slow processing:** Large PDFs or first-time run

---

### <span style="color:#0097A7">Perfect For</span>
- 🎓 Students
- 📖 Researchers
- 👷 Professionals
- 💬 Study groups

---

<p align="center"><strong>
Built with <span style="color:#FF4F4F;">❤️</span> for Chemical Engineers  
Powered by <span style="color:#4A90E2;">Google Gemini</span>, <span style="color:#028A0F;">ChromaDB</span>, and <span style="color:#FFC107;">Streamlit</span>
</strong></p>
