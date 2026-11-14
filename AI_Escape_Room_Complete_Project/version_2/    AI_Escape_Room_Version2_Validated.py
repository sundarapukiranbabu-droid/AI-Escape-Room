import time
import streamlit as st
from streamlit_autorefresh import st_autorefresh

try:
    from google import genai
except ImportError:
    genai = None

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="AI Escape Room",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Refresh the app every second so the countdown timer updates automatically.
st_autorefresh(interval=1000, key="escape_room_timer_refresh")

# ---------------- STYLING ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Inter:wght@400;500;600;700&display=swap');
.stApp {
    background:
      radial-gradient(circle at 15% 10%, rgba(25, 90, 150, .20), transparent 30%),
      radial-gradient(circle at 85% 85%, rgba(125, 45, 180, .18), transparent 35%),
      #080d18;
    color: #edf4ff;
    font-family: 'Inter', sans-serif;
}
h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; }
.hero {
    padding: 28px 30px; border: 1px solid #24466d; border-radius: 20px;
    background: linear-gradient(120deg, rgba(15,35,65,.96), rgba(35,18,62,.92));
    box-shadow: 0 0 28px rgba(0,180,255,.12);
}
.hero-title {
    font-family: 'Orbitron', sans-serif; font-size: clamp(28px, 4vw, 46px);
    font-weight: 900; letter-spacing: 1px; color: #f4f9ff;
}
.hero-sub { color: #9fc8ef; font-size: 16px; margin-top: 8px; }
.metric-card {
    background: linear-gradient(145deg, #111e32, #101526);
    border: 1px solid #29466b; border-radius: 15px; padding: 16px;
}
.metric-label { color: #8faacb; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }
.metric-value { color: #6ee7ff; font-family: 'Orbitron', sans-serif; font-size: 25px; font-weight: 700; }
.room-card {
    border: 1px solid #28405e; border-radius: 15px; padding: 16px;
    background: rgba(14, 25, 43, .88); min-height: 115px;
}
.room-card strong { color: #8be9ff; }
.stButton > button {
    border-radius: 10px; border: 1px solid #2878ad; color: white;
    background: linear-gradient(90deg, #075985, #4338a5);
    font-weight: 700; transition: .2s ease;
}
.stButton > button:hover { box-shadow: 0 0 16px rgba(56,189,248,.55); border-color: #67e8f9; }
div[data-testid="stChatMessage"] {
    background: rgba(17, 31, 52, .85); border: 1px solid #233d5c;
    border-radius: 14px; padding: 8px 12px;
}
section[data-testid="stSidebar"] {
    background: #0b1423; border-right: 1px solid #203b5d;
}
small, .muted { color: #9bb2ce; }
</style>
""", unsafe_allow_html=True)

# ---------------- GAME DATA ----------------
DIFFICULTIES = {
    "Easy": {"seconds": 900, "hints": 5, "points": 100},
    "Medium": {"seconds": 720, "hints": 3, "points": 150},
    "Hard": {"seconds": 600, "hints": 2, "points": 200},
}
PUZZLES = [
    ("Bookshelf", "Find the four numbered books and read their sequence from left to right.", "1234"),
    ("Painting", "Inspect the painting carefully. The message says: LOOK BEHIND THE PAINTING. Find the small brass key.", "key"),
    ("Desk", "The note on the desk reveals the four-digit exit code.", "2468"),
    ("Exit Door", "Use the brass key and the four-digit code to unlock the exit.", "2468"),
]

def reset_game(difficulty):
    cfg = DIFFICULTIES[difficulty]
    st.session_state.difficulty = difficulty
    st.session_state.started_at = time.time()
    st.session_state.time_limit = cfg["seconds"]
    st.session_state.hints_left = cfg["hints"]
    st.session_state.score = cfg["points"]
    st.session_state.stage = 0
    st.session_state.has_key = False
    st.session_state.drawer_open = False
    st.session_state.has_code = False
    st.session_state.won = False
    st.session_state.game_over = False
    st.session_state.messages = [{
        "role": "assistant",
        "content": (
            "Welcome to **The Mystery of the Locked Library**. You wake up in a locked library. "
            "Explore the Bookshelf, Painting, Locked Drawer, Desk and Exit Door. Tell me what you want to investigate, "
            "or use the puzzle panel to submit an answer. Your escape begins now!"
        )
    }]

def remaining_seconds():
    return max(0, int(st.session_state.time_limit - (time.time() - st.session_state.started_at)))

def add_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})

# ---------------- SESSION STATE ----------------
if "started_at" not in st.session_state:
    reset_game("Medium")

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("## 🔐 CONTROL PANEL")
    st.caption("THE MYSTERY OF THE LOCKED LIBRARY")
    selected_difficulty = st.selectbox(
        "Difficulty",
        list(DIFFICULTIES.keys()),
        index=list(DIFFICULTIES.keys()).index(st.session_state.difficulty),
    )
    if selected_difficulty != st.session_state.difficulty:
        reset_game(selected_difficulty)
        st.rerun()

    st.markdown("---")
    st.markdown("### 🧩 Room objects")
    objects = [
        ("📚", "Bookshelf", st.session_state.stage >= 1),
        ("🖼️", "Painting", st.session_state.has_key),
        ("🗃️", "Locked Drawer", st.session_state.drawer_open),
        ("📝", "Desk", st.session_state.has_code),
        ("🚪", "Exit Door", st.session_state.won),
    ]
    for icon, name, done in objects:
        status = "✅" if done else "🔒"
        st.write(f"{icon} **{name}**  {status}")

    st.markdown("---")
    st.markdown("### 🎒 Inventory")
    if st.session_state.has_key:
        st.write("🗝️ Brass key")
    else:
        st.caption("No items collected yet.")
    if st.session_state.has_code:
        st.write("📜 Exit code discovered")
    st.markdown("---")
    api_key = st.text_input("Gemini API key (optional)", type="password",
                            help="Used for AI-generated story responses. The game also works without it.")
    model_name = st.text_input("Gemini model", value="gemini-3.5-flash-lite")
    if st.button("🔄 Restart game", use_container_width=True):
        reset_game(st.session_state.difficulty)
        st.rerun()
    st.caption("Your API key is used only during this app session.")

# ---------------- HEADER ----------------
st.markdown("""
<div class="hero">
  <div class="hero-title">🔐 AI ESCAPE ROOM</div>
  <div style="font-family:Orbitron,sans-serif;color:#8be9ff;font-size:18px;margin-top:8px;">
    THE MYSTERY OF THE LOCKED LIBRARY
  </div>
  <div class="hero-sub">Explore clues. Solve puzzles. Beat the clock. Escape the library.</div>
</div>
""", unsafe_allow_html=True)

# ---------------- METRICS ----------------
left, mid, right, extra = st.columns(4)
secs = remaining_seconds()
with left:
    st.markdown(f'<div class="metric-card"><div class="metric-label">⏱ Time remaining</div><div class="metric-value">{secs//60:02d}:{secs%60:02d}</div></div>', unsafe_allow_html=True)
with mid:
    st.markdown(f'<div class="metric-card"><div class="metric-label">🏆 Score</div><div class="metric-value">{st.session_state.score}</div></div>', unsafe_allow_html=True)
with right:
    st.markdown(f'<div class="metric-card"><div class="metric-label">💡 Hints left</div><div class="metric-value">{st.session_state.hints_left}</div></div>', unsafe_allow_html=True)
with extra:
    st.markdown(f'<div class="metric-card"><div class="metric-label">🎯 Puzzle progress</div><div class="metric-value">{min(st.session_state.stage,5)}/5</div></div>', unsafe_allow_html=True)

if secs == 0 and not st.session_state.won:
    st.session_state.game_over = True

st.progress(min(st.session_state.stage / 5, 1.0), text="Escape progress")

# ---------------- ROOM + PUZZLE PANEL ----------------
room_col, puzzle_col = st.columns([1.05, 1])
with room_col:
    st.markdown("### 🏛️ Explore the library")
    a, b = st.columns(2)
    with a:
        st.markdown('<div class="room-card">📚<br><strong>Bookshelf</strong><br><small>Four worn books stand out.</small></div>', unsafe_allow_html=True)
        st.markdown('<div class="room-card">🗃️<br><strong>Locked Drawer</strong><br><small>Use the brass key to open it.</small></div>', unsafe_allow_html=True)
    with b:
        st.markdown('<div class="room-card">🖼️<br><strong>Painting</strong><br><small>A landscape painting hangs crookedly.</small></div>', unsafe_allow_html=True)
        st.markdown('<div class="room-card">🚪<br><strong>Exit Door</strong><br><small>A keypad and a heavy keyhole secure it.</small></div>', unsafe_allow_html=True)

with puzzle_col:
    st.markdown("### 🧠 Puzzle console")
    if st.session_state.stage == 0:
        st.info("Puzzle 1 — Bookshelf: What four-digit sequence do the numbered books reveal?")
        answer = st.text_input("Enter the bookshelf sequence", key="answer_books", max_chars=8)
        if st.button("Submit bookshelf answer"):
            if answer.strip() == "1234":
                st.session_state.stage = 1
                st.session_state.score += 100
                add_message("assistant", "Correct! The books reveal **1-2-3-4**. You notice a faint message near the painting: *LOOK BEHIND THE PAINTING.*")
            else:
                st.session_state.score = max(0, st.session_state.score - 10)
                add_message("assistant", "That sequence doesn't fit. Re-examine the four special books on the third shelf. (10 points deducted.)")
            st.rerun()
    elif st.session_state.stage == 1:
        st.info("Puzzle 2 — Painting: What should you do after reading the hidden message?")
        if st.button("Look behind the painting"):
            st.session_state.has_key = True
            st.session_state.stage = 2
            st.session_state.score += 100
            add_message("assistant", "You move the painting and discover a **small brass key** hidden behind it. The key may fit the locked drawer.")
            st.rerun()
    elif st.session_state.stage == 2:
        st.info("Puzzle 3 — Locked Drawer: The brass key may fit the old drawer lock.")
        st.write("You found a small brass key behind the painting. Try it on the locked drawer.")
        if st.button("🗝️ Use brass key on the locked drawer"):
            if st.session_state.has_key:
                st.session_state.drawer_open = True
                st.session_state.stage = 3
                st.session_state.score += 75
                add_message("assistant", "The key turns smoothly. The drawer opens! Inside you find a folded note on the desk with a four-digit code.")
            else:
                add_message("assistant", "The drawer is still locked. You need to find its brass key first.")
            st.rerun()
    elif st.session_state.stage == 3:
        st.info("Puzzle 4 — Desk: Read the note found in the unlocked drawer and enter its four-digit code.")
        st.markdown("📜 **Desk note:** The code is an even-number sequence: 2, 4, 6, 8.")
        answer = st.text_input("Enter the desk code", key="answer_desk", max_chars=8)
        if st.button("Submit desk code"):
            if answer.strip() == "2468":
                st.session_state.has_code = True
                st.session_state.stage = 4
                st.session_state.score += 100
                add_message("assistant", "Correct! The note reveals **2468**. You now have the brass key and the exit code.")
            else:
                st.session_state.score = max(0, st.session_state.score - 10)
                add_message("assistant", "Incorrect code. Re-read the note found inside the unlocked drawer. (10 points deducted.)")
            st.rerun()
    elif st.session_state.stage == 4:
        st.success("Final challenge — Exit Door")
        st.write("Use the brass key and the four-digit code to unlock the door.")
        code = st.text_input("Enter the exit code", max_chars=8)
        if st.button("🚪 UNLOCK THE EXIT"):
            if st.session_state.has_key and st.session_state.has_code and code.strip() == "2468":
                st.session_state.stage = 5
                st.session_state.won = True
                st.session_state.score += 250
                add_message("assistant", "🎉 **The lock clicks open! You escaped the Mystery of the Locked Library. Congratulations, Master Escape Artist!**")
            else:
                st.session_state.score = max(0, st.session_state.score - 20)
                add_message("assistant", "The door remains locked. You must have the brass key and solve the desk code first. (20 points deducted.)")
            st.rerun()
    else:
        st.success("🏆 ESCAPE SUCCESSFUL!")
        st.balloons()
        st.markdown(f"### Final score: {st.session_state.score}")
        st.write("You solved every puzzle and escaped the library!")

# ---------------- HINTS ----------------
hint_texts = {
    0: "The four special books are numbered in order. Read them from left to right.",
    1: "The painting's hidden message says to look behind it. The brass key is there.",
    2: "You already have the brass key. Use it on the locked drawer.",
    3: "Read the note found in the drawer. It gives an even-number sequence.",
    4: "The exit requires the brass key and the four-digit code from the note.",
}
if st.session_state.stage < 5 and not st.session_state.game_over:
    if st.button("💡 Request a hint"):
        if st.session_state.hints_left > 0:
            st.session_state.hints_left -= 1
            st.session_state.score = max(0, st.session_state.score - 25)
            add_message("assistant", f"💡 Hint: {hint_texts[st.session_state.stage]} (25 points deducted.)")
        else:
            add_message("assistant", "You have used all your hints. Keep exploring the room!")
        st.rerun()

# ---------------- CHAT / AI STORYTELLER ----------------
st.markdown("---")
st.markdown("### 💬 Talk to the AI Game Master")
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if not st.session_state.won and not st.session_state.game_over:
    player_input = st.chat_input("Ask about an object, request guidance, or describe what you want to do...")
    if player_input:
        add_message("user", player_input)
        lower = player_input.lower()
        local_reply = None

        if any(word in lower for word in ["bookshelf", "books", "shelf"]):
            local_reply = "You see four worn books on the third shelf. Their numbers form a sequence. Inspect them and submit the sequence in the Puzzle Console."
        elif any(word in lower for word in ["painting", "picture", "behind"]):
            local_reply = "The painting hangs slightly crooked. A faint message says: LOOK BEHIND THE PAINTING. Use the Painting action in the Puzzle Console."
        elif any(word in lower for word in ["drawer", "locked drawer"]):
            if st.session_state.drawer_open:
                local_reply = "The drawer is open. You found a folded note inside it. Read the note at the Desk puzzle console to get the exit code."
            elif st.session_state.has_key:
                local_reply = "You have the brass key. Use it on the locked drawer in the Puzzle Console."
            else:
                local_reply = "The drawer has an old brass lock. Search behind the painting to find its key."
        elif any(word in lower for word in ["desk", "note"]):
            if st.session_state.drawer_open:
                local_reply = "The note inside the drawer shows an even-number sequence. Enter the four digits at the Desk puzzle console."
            else:
                local_reply = "The desk note is secured inside the locked drawer. Find the brass key behind the painting first."
        elif any(word in lower for word in ["door", "exit", "escape"]):
            local_reply = "The exit door has a keyhole and a keypad. Find the brass key behind the painting, use it to open the drawer, then read the note for the exit code."
        elif "hint" in lower:
            local_reply = hint_texts.get(st.session_state.stage, "You have already escaped.")
        else:
            local_reply = "Look closely at the room's objects. Try investigating the bookshelf, painting, desk, locked drawer, or exit door."

        if api_key and genai is not None:
            try:
                client = genai.Client(api_key=api_key)
                prompt = (
                    "You are a concise, atmospheric escape-room game master. Stay within this story. "
                    "Do not invent solved puzzles, items, or progress. Never claim the player escaped. "
                    "The local game engine controls puzzle progress. Give a helpful in-character response "
                    "based on this known state: "
                    f"stage={st.session_state.stage}, brass_key={st.session_state.has_key}, "
                    f"drawer_open={st.session_state.drawer_open}, desk_code_found={st.session_state.has_code}. "
                    f"Player says: {player_input!r}. Suggested factual guidance: {local_reply}"
                )
                response = client.models.generate_content(model=model_name, contents=prompt)
                if response.text:
                    local_reply = response.text
            except Exception:
                local_reply += "\n\n_(AI service is unavailable right now; the built-in game guide is still working.)_"

        add_message("assistant", local_reply)
        st.rerun()

if st.session_state.game_over:
    st.error("⏰ TIME'S UP! The library remains locked. Restart the game to try again.")
    if st.button("Try again"):
        reset_game(st.session_state.difficulty)
        st.rerun()

st.caption("Tip: The timer updates whenever the app refreshes or you interact. Keep this tab active while playing.")
