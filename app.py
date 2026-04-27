import streamlit as st
from openai import OpenAI
import sqlite3
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="MindMate AI", page_icon="🧠", layout="wide")

# --- DATABASE SETUP (SQLite) ---
# Connect to a local file called 'mindmate.db'
conn = sqlite3.connect('mindmate.db', check_same_thread=False)
c = conn.cursor()

# Create our two tables if they don't already exist
c.execute('''CREATE TABLE IF NOT EXISTS chats 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, content TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS moods 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, score INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
conn.commit()

# Database Helper Functions
def save_chat(role, content):
    c.execute("INSERT INTO chats (role, content) VALUES (?, ?)", (role, content))
    conn.commit()

def save_mood(score):
    c.execute("INSERT INTO moods (score) VALUES (?)", (score,))
    conn.commit()

def load_chats():
    c.execute("SELECT role, content FROM chats")
    return [{"role": row[0], "content": row[1]} for row in c.fetchall()]

def load_moods():
    c.execute("SELECT score FROM moods")
    return [row[0] for row in c.fetchall()]

# --- GROQ API SETUP ---
my_groq_key = st.secrets["GROQ_API_KEY"] # Reads from Streamlit Cloud Secrets

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

# --- INITIALIZE MEMORY FROM DATABASE ---
if "messages" not in st.session_state:
    saved_chats = load_chats()
    if len(saved_chats) == 0:
        # If DB is empty, start with the hidden system prompt
        st.session_state.messages = [{
            "role": "system", 
            "content": "You are an empathetic mental health companion. You use CBT techniques. Keep answers brief and warm. Do not diagnose."
        }]
    else:
        # Load history from DB
        st.session_state.messages = saved_chats

if "mood_trend" not in st.session_state:
    st.session_state.mood_trend = load_moods()

# --- SIDEBAR: THE WELLNESS DASHBOARD ---
with st.sidebar:
    st.title("🌱 Your Wellness Dashboard")
    
    st.subheader("How are you feeling right now?")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("😊 Good"):
            st.session_state.mood_trend.append(3)
            save_mood(3) # Save to Database
            st.success("Glad to hear you're feeling good!")
    with col2:
        if st.button("😐 Okay"):
            st.session_state.mood_trend.append(2)
            save_mood(2) # Save to Database
            st.info("It's okay to just be okay.")
    with col3:
        if st.button("😔 Down"):
            st.session_state.mood_trend.append(1)
            save_mood(1) # Save to Database
            st.warning("I'm sorry you're feeling down.")
            
    # Draw Graph
    if len(st.session_state.mood_trend) > 0:
        st.write("📈 **Your Mood Trend**")
        st.line_chart(st.session_state.mood_trend)

    st.divider()
    
    st.subheader("Quick Relief Tool")
    if st.button("🌬️ 1-Minute Breathing Exercise"):
        st.write("**Box Breathing:** 4s In, 4s Hold, 4s Out, 4s Hold. Repeat.")

    st.divider()
    
    st.subheader("🚨 Emergency Resources")
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
    
    # Save User Message
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    save_chat("user", user_input) # Save to Database

    # Guardrail Check
    if is_unsafe(user_input):
        safety_msg = "I am concerned about you. Please call the Suicide & Crisis Lifeline at 988 immediately."
        with st.chat_message("assistant"):
            st.error(safety_msg)
        st.session_state.messages.append({"role": "assistant", "content": safety_msg})
        save_chat("assistant", safety_msg) # Save to Database
    
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
                
                # Save AI Message
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                save_chat("assistant", full_response) # Save to Database
                
            except Exception as e:
                st.error(f"API Error: {e}")
