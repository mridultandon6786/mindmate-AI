import streamlit as st
from openai import OpenAI

# --- CONFIGURATION ---
st.set_page_config(page_title="MindMate AI", page_icon="🧠", layout="wide")

# --- GROQ API SETUP ---
my_groq_key = st.secrets["GROQ_API_KEY"]

client = OpenAI(
    api_key=my_groq_key,
    base_url="https://api.groq.com/openai/v1"
)

# --- SAFETY FILTER ---
def is_unsafe(text):
    risk_keywords = ["suicide", "kill myself", "end it", "hurt myself", "die"]
    for word in risk_keywords:
        if word in text.lower():
            return True
    return False

# --- INITIALIZE MEMORY & DATA ---
# This setup happens before anything is drawn on screen
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "system", 
        "content": "You are an empathetic mental health companion. You use CBT techniques. Keep answers brief and warm. Do not diagnose."
    })

# Create a list to store mood scores
if "mood_trend" not in st.session_state:
    st.session_state.mood_trend = []

# --- SIDEBAR: THE WELLNESS DASHBOARD ---
with st.sidebar:
    st.title("🌱 Your Wellness Dashboard")
    
    # 1. Mood Tracker
    st.subheader("How are you feeling right now?")
    col1, col2, col3 = st.columns(3)
    
    # We assign 3=Good, 2=Okay, 1=Down to make a graph
    with col1:
        if st.button("😊 Good"):
            st.session_state.mood_trend.append(3)
            st.success("Glad to hear you're feeling good!")
    with col2:
        if st.button("😐 Okay"):
            st.session_state.mood_trend.append(2)
            st.info("It's okay to just be okay.")
    with col3:
        if st.button("😔 Down"):
            st.session_state.mood_trend.append(1)
            st.warning("I'm sorry you're feeling down.")
            
    # Draw the Live Graph if there is data
    if len(st.session_state.mood_trend) > 0:
        st.write("📈 **Your Mood Trend**")
        # Streamlit automatically turns a list of numbers into a line chart!
        st.line_chart(st.session_state.mood_trend)

    st.divider()
    
    # 2. Quick Exercises
    st.subheader("Quick Relief Tool")
    if st.button("🌬️ 1-Minute Breathing Exercise"):
        st.write("**Box Breathing:**")
        st.write("1. Breathe in for 4 seconds.")
        st.write("2. Hold your breath for 4 seconds.")
        st.write("3. Breathe out for 4 seconds.")
        st.write("4. Hold for 4 seconds.")
        st.write("*Repeat 4 times.*")

    st.divider()
    
    # 3. Emergency Resources
    st.subheader("🚨 Emergency Resources")
    st.write("If you are in crisis, please reach out:")
    st.write("**Suicide & Crisis Lifeline:** 988")
    st.write("**Crisis Text Line:** Text HOME to 741741")

# --- MAIN APP INTERFACE ---
st.title("🧠 MindMate")
st.caption("I am here to listen. Note: I am an AI, not a doctor.")

# Display Chat History
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- CHAT LOGIC ---
if user_input := st.chat_input("What's on your mind today?"):
    
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Guardrail Check
    if is_unsafe(user_input):
        safety_msg = "I am concerned about you. Please call the Suicide & Crisis Lifeline at 988 immediately."
        with st.chat_message("assistant"):
            st.error(safety_msg)
        st.session_state.messages.append({"role": "assistant", "content": safety_msg})
    
    # AI Response
    else:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                stream = client.chat.completions.create(
                    model="llama-3.1-8b-instant", 
                    messages=st.session_state.messages,
                    stream=True,
                )
                
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                        message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                st.error(f"API Error: {e}")