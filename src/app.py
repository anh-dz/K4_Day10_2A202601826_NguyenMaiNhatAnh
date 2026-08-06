import streamlit as st
import json
from pathlib import Path

from core.config import load_settings
from retrieval.index import LocalEmbeddingIndex
from retrieval.agent import build_agent, run_agent_question

# Cấu hình UI
st.set_page_config(page_title="VinAI RAG Dashboard", page_icon="📊", layout="wide")

# Cấu hình Path
PROJECT_DIR = Path(__file__).parent.parent
REPORT_DIR = PROJECT_DIR / "data" / "reports"

# Tải tài nguyên
@st.cache_resource
def get_agent_and_index():
    settings = load_settings()
    index = LocalEmbeddingIndex.load(settings)
    agent = build_agent(settings, index)
    return settings, agent, index

try:
    settings, agent, index = get_agent_and_index()
    agent_ready = True
except Exception as e:
    agent_ready = False
    error_msg = str(e)

st.title("VinAI RAG Observability Dashboard 🚀")

tab1, tab2 = st.tabs(["💬 Trợ lý RAG (Agent Chat)", "📈 Báo Cáo Chất Lượng (Observability)"])

with tab1:
    st.header("Trò chuyện với Kho dữ liệu Bài báo")
    
    if not agent_ready:
        st.error(f"Không thể tải hệ thống RAG Agent. Lỗi: {error_msg}\nVui lòng chạy Ingestion Pipeline trước!")
    else:
        # Lưu trữ lịch sử chat
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Hiển thị lịch sử chat
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Xử lý input người dùng
        if prompt := st.chat_input("Hỏi tôi bất kỳ điều gì về các bài báo..."):
            # Lưu và hiển thị câu hỏi
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Trả lời
            with st.chat_message("assistant"):
                from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
                
                st_callback = StreamlitCallbackHandler(st.container())
                try:
                    # Chạy agent với callback để hiển thị log "Thinking..."
                    result = agent.invoke(
                        {"messages": [{"role": "user", "content": prompt}]},
                        config={"callbacks": [st_callback]}
                    )
                    messages = result.get("messages", [])
                    final_message = messages[-1] if messages else ""
                    response = getattr(final_message, "content", str(final_message))
                    st.markdown(response)
                except Exception as e:
                    response = f"❌ Đã xảy ra lỗi: {str(e)}"
                    st.markdown(response)
                    
            st.session_state.messages.append({"role": "assistant", "content": response})

with tab2:
    st.header("Báo Cáo So Sánh Baseline vs. Corrupted vs. Repaired")
    
    report_file = REPORT_DIR / "comparison_report.md"
    chart_file = REPORT_DIR / "comparison_chart.png"
    
    if report_file.exists():
        with open(report_file, "r", encoding="utf-8") as f:
            content = f.read()
            
            # Xóa dòng nhúng ảnh trong Markdown vì Streamlit hiển thị ảnh riêng sẽ đẹp hơn
            content = content.replace("![Comparison Chart](./comparison_chart.png)", "")
            st.markdown(content)
            
        if chart_file.exists():
            st.image(str(chart_file), caption="Biểu đồ so sánh chất lượng mô hình (Metrics Comparison)")
    else:
        st.warning("Chưa có báo cáo so sánh. Vui lòng chạy luồng Corruption (uv run python script/cli.py corruption) để tạo báo cáo.")
