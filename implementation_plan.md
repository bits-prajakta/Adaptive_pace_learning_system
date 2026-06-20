# Implementation Plan: Navigation, High-Contrast UI, Real Google Meets, and LLM Indicators

This plan details the revisions to the **Adaptive Pace Learning System** to address UI contrast, navigation loop issues, Google Meet URL authenticity, reminders, and Gemini AI activation feedback.

## User Review Required

> [!IMPORTANT]
> - **High-Contrast Styling**: We will override Streamlit's default button classes (`stButton`) using custom CSS in `app.py`. Primary buttons will have a bright blue/green background with white bold text, and secondary buttons will have a clean dark background with a highlighted border and white text.
> - **Real Google Meets**: We will add a helper link `meet.google.com/new` in the hosting form so users can easily start a real meeting, copy the link, and paste it into the system.
> - **Reminders**: A new database query will retrieve upcoming meetings for topics the user is enrolled in, showing them in the sidebar and dashboard.

---

## Proposed Changes

### 1. Core Styles & LLM Indicator (`app.py`)
- **Button Contrast**: Inject custom CSS rules to enforce clear white text (`#FFFFFF`) on all button states (hover, focus, active).
- **LLM Status Indicator**: Render a visual status block in the sidebar:
  - If `st.session_state.gemini_key` is empty: display a grey/yellow badge `⚠️ Local Template Mode` with a tooltip.
  - If `st.session_state.gemini_key` is provided: display a glowing green badge `🟢 Gemini AI Active` with explanation of its usage.

### 2. Quiz Exit & Reset Logic (`views/quiz.py`)
- **Quit Button**: Add a red `🚪 Quit Quiz` button next to the game status bar.
- **State Cleanup**: Clicking it calls `clean_quiz_state()` and reruns, immediately placing the user back in search mode.
- **Search Landing**: Ensure that if `quiz_active` is False and `quiz_completed` is False, the topic search text field is cleared or ready for input.

### 3. Real Meets & Notification Reminders (`views/study_group.py` & `views/dashboard.py`)
- **Meet Hosting Form**:
  - Replace the auto-generated link field with an input text box: "Meet Link (e.g. from meet.google.com/new)".
  - Add a button "Create Instant Google Meet 🔗" which opens `https://meet.google.com/new` in a new tab so they can copy the real room URL.
  - If the link field is left empty, automatically generate a mockup code so it still works.
- **Reminders Panel**:
  - Implement a query `get_upcoming_reminders(username)` that returns meetings scheduled by others on the user's topics.
  - Display reminders as card alerts on the Dashboard and in the sidebar.

---

## Verification Plan

### Automated Tests
We will update `test_pace_model.py` to ensure all database utilities and schemas (specifically `meet_invitations` updates) compile and run without errors.

### Manual Verification
- Verify button labels are readable.
- Start a quiz, navigate to Dashboard, click back to Quiz Arena, and verify it resumes.
- Click `Quit Quiz` during an active quiz and verify it successfully resets back to the Search screen.
- Enter a dummy API key in the sidebar and check if the indicator updates to `🟢 Gemini AI Active`.
- Host a meeting by creating a real room, paste the link, click on it from another account, and verify it launches the correct room.
