import os
import time
import tempfile
import streamlit as st
from pages_ui.components import page_header, render_meeting_result, save_to_history


def render():
    page_header("🎙️", "Meeting Mode", "Record, upload, or paste a meeting transcript")

    # ── Input method selector ─────────────────────────────────────────────────
    st.markdown("**How do you want to provide the audio?**")
    input_method = st.radio(
        "Input method",
        ["📁 Upload audio file", "📋 Paste transcript text", "🎤 Record live (mic)"],
        label_visibility="collapsed",
        horizontal=True
    )

    transcript = None
    duration   = 0.0

    # ── Upload ────────────────────────────────────────────────────────────────
    if "Upload" in input_method:
        uploaded = st.file_uploader(
            "Upload meeting audio",
            type=["wav", "mp3", "m4a", "mp4", "ogg", "flac"],
            help="Whisper supports most common audio formats"
        )
        if uploaded:
            st.markdown(f'<div class="notify notify-info">📂 File loaded: <b>{uploaded.name}</b> ({uploaded.size / 1024:.1f} KB)</div>', unsafe_allow_html=True)

            if st.button("▶ Transcribe with Whisper", use_container_width=True):
                with st.status("🔊 Transcribing audio with Whisper...", expanded=True) as status:
                    try:
                        # Save upload to temp file
                        suffix = os.path.splitext(uploaded.name)[1]
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                        tmp.write(uploaded.read())
                        tmp.close()

                        st.write("Loading Whisper model...")
                        from transcriber import transcribe_audio
                        transcript, duration = transcribe_audio(tmp.path if hasattr(tmp, 'path') else tmp.name)
                        os.unlink(tmp.name)

                        st.session_state["meeting_transcript"] = transcript
                        st.session_state["meeting_duration"]   = duration
                        status.update(label="✅ Transcription complete!", state="complete")
                    except Exception as e:
                        status.update(label=f"❌ Error: {e}", state="error")

    # ── Paste ─────────────────────────────────────────────────────────────────
    elif "Paste" in input_method:
        pasted = st.text_area(
            "Paste your transcript here",
            height=220,
            placeholder="Paste your meeting transcript, Zoom auto-transcript, or any meeting notes here...",
        )
        if pasted and len(pasted.strip()) > 50:
            st.session_state["meeting_transcript"] = pasted
            st.session_state["meeting_duration"]   = len(pasted.split()) / 130
            st.markdown('<div class="notify notify-success">✅ Transcript ready to process</div>', unsafe_allow_html=True)

    # ── Record ────────────────────────────────────────────────────────────────
    elif "Record" in input_method:
        st.markdown("""
        <div class="notify notify-info">
            🎤 Live recording uses your microphone. Click Start, speak, then Stop.
            <br>Requires <code>sounddevice</code> to be installed.
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            duration_input = st.number_input("Max duration (minutes)", min_value=1, max_value=120, value=5)
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔴 Start Recording", use_container_width=True):
                with st.status("🎙️ Recording... (press Stop or wait for timeout)", expanded=True) as status:
                    try:
                        from transcriber import record_audio, transcribe_audio
                        audio_path = record_audio(duration_seconds=duration_input * 60)
                        st.write("Transcribing with Whisper...")
                        transcript, duration = transcribe_audio(audio_path)
                        os.unlink(audio_path)
                        st.session_state["meeting_transcript"] = transcript
                        st.session_state["meeting_duration"]   = duration
                        status.update(label="✅ Recording and transcription done!", state="complete")
                    except Exception as e:
                        status.update(label=f"❌ {e}", state="error")

    # ── Show transcript preview if ready ─────────────────────────────────────
    transcript = st.session_state.get("meeting_transcript", "")
    duration   = st.session_state.get("meeting_duration", 0.0)

    if transcript:
        with st.expander("📄 View transcript preview", expanded=False):
            st.text_area("Transcript", transcript[:2000] + ("..." if len(transcript) > 2000 else ""),
                         height=150, disabled=True, label_visibility="collapsed")
            st.caption(f"{len(transcript.split()):,} words | ~{duration:.1f} min")

        st.markdown("---")

        # ── Run AI Extraction ─────────────────────────────────────────────
        st.markdown("**AI Extraction Settings**")
        col1, col2 = st.columns(2)
        with col1:
            extract_tasks_cb    = st.checkbox("Extract action items & tasks", value=True)
        with col2:
            extract_summary_cb  = st.checkbox("Generate meeting summary", value=True)

        if st.button("🤖 Run AI Extraction", use_container_width=True, type="primary"):
            with st.status("🤖 Running Gemini AI extraction...", expanded=True) as status:
                try:
                    import time as t
                    start = t.time()

                    from gemini import (extract_tasks, extract_meeting_summary,
                                        deduplicate_tasks, calculate_accuracy)

                    tasks_obj = None
                    summary   = None

                    if extract_tasks_cb:
                        st.write("Extracting tasks and action items...")
                        raw_tasks = extract_tasks(transcript)
                        tasks_obj = deduplicate_tasks(raw_tasks)

                    if extract_summary_cb:
                        st.write("Generating meeting summary...")
                        summary = extract_meeting_summary(transcript)

                    proc_time = t.time() - start
                    accuracy  = calculate_accuracy(tasks_obj) if tasks_obj else 0

                    result = {
                        "tasks":           tasks_obj,
                        "summary":         summary,
                        "accuracy":        accuracy,
                        "processing_time": proc_time,
                        "duration":        duration,
                    }
                    st.session_state["meeting_result"] = result
                    status.update(label=f"✅ Done in {proc_time:.1f}s!", state="complete")

                except Exception as e:
                    status.update(label=f"❌ Error: {e}", state="error")
                    st.exception(e)

    # ── Results ───────────────────────────────────────────────────────────────
    result = st.session_state.get("meeting_result")
    if result:
        st.markdown("---")
        st.markdown("""
        <div style="font-family:'Syne',sans-serif; font-size:1.1rem; font-weight:700;
                    color:#60A5FA; margin-bottom:1rem;">📊 Results</div>
        """, unsafe_allow_html=True)

        render_meeting_result(result)

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📤 Push to Notion", use_container_width=True):
                with st.status("Pushing to Notion...", expanded=True) as status:
                    try:
                        from push_to_notion import push_meeting
                        push_meeting(result["tasks"], result["summary"])
                        status.update(label="✅ Pushed to Notion!", state="complete")
                        save_to_history("meeting", result["summary"].title if result.get("summary") else "Meeting", result)
                        st.markdown('<div class="notify notify-success">✅ Successfully saved to Notion!</div>', unsafe_allow_html=True)
                    except Exception as e:
                        status.update(label=f"❌ {e}", state="error")

        with col2:
            if st.button("🗑️ Clear & Start Over", use_container_width=True):
                for k in ["meeting_transcript", "meeting_duration", "meeting_result"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()