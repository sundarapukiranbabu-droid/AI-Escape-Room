import streamlit as st
from google import genai

# -----------------------------
# PAGE CONFIGURATION
# -----------------------------

st.set_page_config(
    page_title="AI Escape Room",
    page_icon="🔐",
    layout="centered"
)

# -----------------------------
# GAME INFORMATION
# -----------------------------

GAME_TITLE = "The Mystery of the Locked Library"

ROOM_OBJECTS = [
    "Desk",
    "Bookshelf",
    "Painting",
    "Locked Drawer",
    "Exit Door"
]

SYSTEM_PROMPT = """
You are the Game Master of an interactive AI Escape Room.

STORY:
The player wakes up inside a mysterious locked library.

ROOM OBJECTS:
1. Desk
2. Bookshelf
3. Painting
4. Locked Drawer
5. Exit Door

PUZZLES:

Puzzle 1:
The bookshelf contains four special books.
Their numbers are 1, 2, 3 and 4.
The player must discover the sequence 1234.

Puzzle 2:
The painting contains a hidden message:
LOOK BEHIND THE PAINTING.
The player discovers a small key.

Puzzle 3:
The desk contains a note explaining that the
final exit requires the four-digit code 2468.

FINAL CHALLENGE:
The player must discover the clues and enter
2468 to escape.

RULES:
    - Act as an intelligent and helpful AI Game Master.
    - Respond naturally and clearly to player messages.
    - Understand the player's questions before responding.
    - Give specific clues related to the actual puzzles.
    - Never give vague or repetitive descriptions.
    - When players inspect an object, explain its relevant clues.
    - When players ask for exact numbers, provide the
      numbers available in the puzzle information.
    - When players request hints, provide useful hints
      without unnecessarily revealing every answer.
    - If players explicitly request a puzzle solution,
      provide the correct answer.
    - Never invent puzzle numbers, clues or objects.
    - Maintain conversation context.
    - Explain incorrect answers politely.
    - Do not claim the player escaped unless the
      required final code has been entered.
    - Keep the game engaging and interactive.
"""

# -----------------------------
# SESSION STATE
# -----------------------------

if "messages" not in st.session_state:

    st.session_state.messages = [
        {
            "role": "assistant",
            "content": """
Welcome to the Mystery of the Locked Library!

You wake up inside an unfamiliar library.
The exit door is locked.

You notice five objects:

📚 Bookshelf
🖼️ Painting
🪑 Desk
🔒 Locked Drawer
🚪 Exit Door

Explore the room and discover clues to escape!

What would you like to investigate first?
"""
        }
    ]

if "chat" not in st.session_state:
    st.session_state.chat = None

# -----------------------------
# SIDEBAR
# -----------------------------

st.sidebar.title("🔐 Game Information")

st.sidebar.write("### Available Objects")

for obj in ROOM_OBJECTS:
    st.sidebar.write("•", obj)

st.sidebar.info(
    "Your mission is to investigate the "
    "library and escape."
)

api_key = st.sidebar.text_input(
    "Gemini API Key",
    type="password",
    help="Your API key is used only for this session."
)

if st.sidebar.button("Restart Game"):
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Welcome back! You are inside the locked library. What would you like to investigate?"
        }
    ]
    st.session_state.chat = None
    st.rerun()

# -----------------------------
# MAIN INTERFACE
# -----------------------------

st.title("🔐 AI Escape Room")

st.subheader(GAME_TITLE)

st.write(
    "Explore the mysterious library, solve puzzles "
    "and find your way out!"
)

st.divider()

# Display conversation history

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -----------------------------
# PLAYER INTERACTION
# -----------------------------

player_input = st.chat_input(
    "What would you like to do?"
)

if player_input:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": player_input
        }
    )

    with st.chat_message("user"):
        st.markdown(player_input)

    with st.chat_message("assistant"):

        if not api_key:

            response_text = (
                "Please enter your Gemini API key "
                "in the sidebar to start playing."
            )

        else:

            try:

                client = genai.Client(
                    api_key=api_key
                )

                conversation = SYSTEM_PROMPT + "\n\n"

                for msg in st.session_state.messages:
                    conversation += (
                        msg["role"].upper()
                        + ": "
                        + msg["content"]
                        + "\n"
                    )

                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=conversation
                )

                response_text = response.text

            except Exception as e:

                response_text = (
                    "Something went wrong while "
                    "connecting to Gemini. Please "
                    "check your API key and try again.\n\n"
                    f"Error: {e}"
                )

        st.markdown(response_text)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response_text
        }
    )
