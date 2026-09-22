"""Detection 工程师 AI 助手 - Streamlit 入口。"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.workflow import DetectionAssistant


st.set_page_config(page_title="Fab Detection AI 助手", page_icon="🔬", layout="wide")
st.markdown("""
<style>
.stApp { background: #f7f8fa; }
.block-container { max-width: 1180px; padding-top: 2rem; }
.hero { padding: 1.2rem 1.4rem; background: linear-gradient(135deg,#102a43,#243b53); color: white; border-radius: 16px; margin-bottom: 1rem; }
.hero h1 { margin: 0; font-size: 2rem; }
.hero p { margin: .45rem 0 0; color: #d9e2ec; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_assistant():
    return DetectionAssistant(str(ROOT / "data" / "knowledge"))


if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.markdown("### Fab Detection AI")
    st.caption("面向 detection / yield / process 工程师的分析助手")
    if st.button("新建对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.markdown("**快速问题**")
    quick_prompts = [
        "分析 LOT-240921-A01 的缺陷情况",
        "查看 INS-07 的 SPC 趋势",
        "查询 INS-07 最近报警",
        "生成 LOT-240921-A01 分析报告",
        "Bridge 和 edge ring 应该怎么排查？",
    ]
    for prompt in quick_prompts:
        if st.button(prompt, key=prompt, use_container_width=True):
            st.session_state.pending_prompt = prompt
            st.rerun()
    st.divider()
    st.caption("当前版本使用演示数据。接入真实 fab 系统前，请先配置数据权限和审计策略。")

st.markdown('<div class="hero"><h1>🔬 Fab Detection 工程师 AI 助手</h1><p>缺陷分析 · SPC 趋势 · 设备报警 · Recipe 变更 · SOP 检索 · 分析报告</p></div>', unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.session_state.pop("pending_prompt", None) or st.chat_input("例如：分析 LOT-240921-A01 的 edge ring 缺陷")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("正在汇总 lot、设备和知识库信息…"):
            result = get_assistant().ask(prompt)
        st.markdown(result["answer"])
    st.session_state.messages.append({"role": "assistant", "content": result["answer"]})
