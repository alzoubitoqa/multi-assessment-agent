"""Streamlit policy evidence and stepwise governance incident demo."""

import json
import streamlit as st

from app.governance.simulator import (
    HUMAN_ACTIONS, get_run_history, list_scenarios, record_human_decision,
    release_next_event, start_scenario,
)
from app.policy.kb import (
    index_policy_documents, load_catalog, search_global_examples, search_policies,
)


def _clear_selected_run() -> None:
    """Avoid showing a previous scenario's events under the new selection."""
    st.session_state.pop("policy_run_id", None)


def render_policy_lab() -> None:
    st.markdown("### ⚖️ ITU Education Policy & Incident Lab")
    st.caption("Synthetic incidents, role-specific information and auditable human-reviewed responses.")
    st.info("Policy records include labelled curated summaries, with optional official PDFs. Foreign policy examples are comparative only. Legal applicability and institutional gaps require independent verification.")

    with st.expander("📚 Policy Knowledge Base", expanded=False):
        st.write(f"**{len(load_catalog())}** source-attributed policy records in the seed catalog")
        if st.button("Build / refresh policy vector index", key="index_policy_vectors"):
            with st.spinner("Indexing policies using local sentence embeddings..."):
                try:
                    result = index_policy_documents()
                    st.success(f"Indexed {result['records_indexed']} policy chunks")
                    if result["missing_pdfs"]:
                        st.warning("Some optional local source PDFs are absent; only available text was indexed.")
                except Exception as exc:
                    st.error(f"Could not index policy documents: {exc}")
        query = st.text_input("Search policy sources", value="student monitoring and academic integrity")
        if query.strip():
            for policy in search_policies(query):
                st.markdown(f"**[{policy['id']}]({policy['url']}) — {policy['reference']}**")
                st.caption(f"{policy['document_type']} · {policy['binding_level']} · {policy['source_kind']} · {policy['retrieval_mode']}")
                st.write(policy["text"])
        st.markdown("**🌍 Global education AI policy examples (comparative only)**")
        for policy in search_global_examples("education assessment human review"):
            st.markdown(f"- [{policy['reference']}]({policy['url']}) — {policy['jurisdiction']} · not automatically applicable in the UAE")

    scenarios = list_scenarios()
    label_to_id = {s["title"]: s["id"] for s in scenarios}
    chosen = st.selectbox("Choose an error scenario", list(label_to_id),
                          key="policy_scenario_choice", on_change=_clear_selected_run)
    st.caption(next(s["description"] for s in scenarios if s["title"] == chosen))

    first, second = st.columns(2)
    with first:
        if st.button("▶️ Start new simulation", key="policy_start", type="primary"):
            st.session_state["policy_run_id"] = start_scenario(label_to_id[chosen])
            st.rerun()
    run_id = st.session_state.get("policy_run_id")
    if not run_id:
        st.write("Start a simulation to reveal the first event. Future events remain hidden.")
        return

    history = get_run_history(run_id)
    if history["scenario_id"] != label_to_id[chosen]:
        st.warning("This run belongs to another scenario. Click Start new simulation to use the current selection.")
        return
    use_llm = st.checkbox("Use source-grounded LLM policy advisers (Groq API required)",
                          value=False, key="policy_llm_enabled")
    with second:
        if st.button("Release next event", key="policy_next",
                     disabled=history["released_count"] >= history["total_events"]):
            try:
                release_next_event(run_id, use_llm=use_llm)
                st.rerun()
            except Exception as exc:
                st.error(f"Could not release event: {exc}")

    st.progress(history["released_count"] / history["total_events"],
                text=f"Released {history['released_count']} / {history['total_events']} events")
    for event in history["events"]:
        st.markdown(f"#### Event {event['number']}: {event['title']}")
        st.write(event["detail"])
        st.caption("Disclosed to: " + ", ".join(event["visible_to"]))
        assessments = [a for a in history["assessments"]
                       if a["observed_event_ids"][-1] == event["id"]]
        for assessment in assessments:
            with st.expander("🤖 " + assessment["role_label"]):
                st.write("**Recommendation:** " + assessment["recommendation"])
                st.caption("Mode: " + assessment["assessment_mode"])
                st.write("**Reviewable rationale:** " + assessment["public_rationale"])
                st.caption("Policy gap status: " + assessment.get("gap_evidence_status", "historical unverified corpus gap"))
                st.caption("Evidence seen: " + ", ".join(assessment["observed_event_ids"]))
                st.write("**Evidence references:**")
                for source in assessment["citations"]:
                    page = f" · page {source['page_number']}" if source.get("page_number") else ""
                    st.markdown(f"- [{source['id']}: {source['reference']}]({source['url']}) — {source['binding_level']} ({source['source_kind']}{page})")
                st.caption("Legal applicability: " + assessment.get("legal_applicability", "not automatically verified"))
                st.warning(assessment["policy_gap"])
        st.divider()

    if history["coordination"]:
        latest = history["coordination"][-1]
        with st.expander("🔗 Latest inter-agent coordination", expanded=True):
            st.write("**Contributors:** " + ", ".join(latest["contributors"]))
            st.write("**Human decision:** " + latest["final_action"])
            st.write("**Potential corpus gaps to verify:** " + "; ".join(latest["unresolved_gaps"]))
            st.write("**Open review checks:** " + "; ".join(latest.get("open_review_questions", [])))
            if latest.get("global_examples"):
                st.markdown("**Global policy comparisons — not binding in the UAE by default:**")
                for source in latest["global_examples"]:
                    st.markdown(f"- [{source['reference']}]({source['url']}) — {source['jurisdiction']}")
            st.caption(latest.get("coordination_limit", "Independent institutional assessments are combined for a human reviewer."))

    if history["released_count"] == history["total_events"]:
        if history["human_decisions"]:
            st.success("Scenario complete. A human review entry has been recorded for this demonstration.")
            for decision in history["human_decisions"]:
                st.write(f"**{decision['action_label']}** — {decision['reviewer']} ({decision['recorded_at']})")
                st.caption(decision["rationale"])
        else:
            st.success("Scenario events complete. A documented human review is still required.")
        st.markdown("#### 👤 Record human review (demo only)")
        st.caption("Reviewer names are self-reported; this prototype does not authenticate institutional authority or change student records.")
        with st.form("policy_human_decision_form", clear_on_submit=True):
            reviewer = st.text_input("Reviewer name / role", max_chars=120)
            action = st.selectbox("Review action", options=list(HUMAN_ACTIONS),
                                  format_func=lambda value: HUMAN_ACTIONS[value])
            rationale = st.text_area("Documented evidence and rationale", max_chars=4000)
            submitted = st.form_submit_button("💾 Record human review")
        if submitted:
            try:
                record_human_decision(run_id, reviewer, action, rationale)
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    st.download_button("⬇️ Download auditable decision trace (JSON)",
                       data=json.dumps(history, ensure_ascii=False, indent=2),
                       file_name=f"policy_incident_{run_id}.json", mime="application/json")
    st.caption("Logs contain released event facts, role assessments, source IDs, and recommendations; they do not expose private model chain-of-thought.")
