import streamlit as st
import requests
import json
from datetime import datetime

# ─── CONFIG ──────────────────────────────────────────────────────────────────
API_BASE = "https://blockchain-based-academic-peer-review.onrender.com"

st.set_page_config(
    page_title="Academic Peer Review System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── STYLES ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .main-header h1 { font-size: 2.2rem; margin: 0; font-weight: 700; }
    .main-header p  { font-size: 1rem; opacity: 0.8; margin: 0.5rem 0 0; }

    .role-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .badge-author   { background:#d4edda; color:#155724; }
    .badge-reviewer { background:#cce5ff; color:#004085; }
    .badge-editor   { background:#fff3cd; color:#856404; }
    .badge-admin    { background:#f8d7da; color:#721c24; }

    .paper-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .paper-card h4 { margin: 0 0 0.3rem; color: #1a1a2e; }
    .paper-card p  { margin: 0; font-size: 0.85rem; color: #555; }

    .status-pill {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .status-Submitted         { background:#e2e8f0; color:#4a5568; }
    .status-Under.Review      { background:#bee3f8; color:#2b6cb0; }
    .status-Reviewed          { background:#fefcbf; color:#744210; }
    .status-Accepted          { background:#c6f6d5; color:#22543d; }
    .status-Rejected          { background:#fed7d7; color:#742a2a; }
    .status-Revision.Required { background:#fbd38d; color:#744210; }

    .metric-card {
        background: #f8f9fa;
        border-left: 4px solid #0f3460;
        border-radius: 6px;
        padding: 1rem;
        text-align: center;
    }
    .metric-card .number { font-size: 2rem; font-weight: 700; color: #0f3460; }
    .metric-card .label  { font-size: 0.8rem; color: #666; text-transform: uppercase; letter-spacing: 0.05em; }

    .tx-hash {
        font-family: monospace;
        font-size: 0.78rem;
        background: #f1f3f5;
        padding: 4px 8px;
        border-radius: 4px;
        word-break: break-all;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
    .sidebar-wallet {
        background: #f0f4ff;
        border-radius: 8px;
        padding: 0.75rem;
        font-family: monospace;
        font-size: 0.78rem;
        word-break: break-all;
        color: #1a1a2e;
    }
</style>
""", unsafe_allow_html=True)

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def api_get(path):
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=10)
        return r.json(), r.status_code
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend. Is the server running on port 3000?"}, 503
    except Exception as e:
        return {"error": str(e)}, 500

def api_post(path, payload):
    try:
        r = requests.post(f"{API_BASE}{path}", json=payload, timeout=15)
        return r.json(), r.status_code
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend. Is the server running on port 3000?"}, 503
    except Exception as e:
        return {"error": str(e)}, 500

def fmt_date(iso_str):
    if not iso_str:
        return "—"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y %H:%M UTC")
    except:
        return iso_str

def status_color(status):
    colors = {
        "Submitted": "#718096",
        "Under Review": "#3182ce",
        "Reviewed": "#d69e2e",
        "Accepted": "#38a169",
        "Rejected": "#e53e3e",
        "Revision Required": "#dd6b20"
    }
    return colors.get(status, "#718096")

def show_paper_card(paper, expanded=False):
    status = paper.get("status", "Submitted")
    color = status_color(status)
    with st.expander(f" {paper.get('title', 'Untitled')}   ·   `{paper.get('originalHash', '')[:16]}...`", expanded=expanded):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"**Abstract:** {paper.get('abstract', '—')}")
            st.markdown(f"**Author Wallet:** `{paper.get('authorWallet', paper.get('author','—'))}`")
        with col2:
            st.markdown(f"**Status**")
            st.markdown(f"<span style='background:{color};color:white;padding:3px 10px;border-radius:10px;font-size:0.8rem;font-weight:600'>{status}</span>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"**Submitted**")
            st.markdown(f"_{fmt_date(paper.get('createdAt', ''))}_")

        if paper.get('ipfsCID'):
            st.markdown(f"**IPFS CID:** `{paper.get('ipfsCID')}`")
        if paper.get('assignedReviewer'):
            st.markdown(f"**Assigned Reviewer:** `{paper.get('assignedReviewer')}`")
        if paper.get('finalDecision'):
            st.markdown(f"**Final Decision:** **{paper.get('finalDecision')}**")

        reviews = paper.get('reviews', [])
        if reviews:
            st.markdown("**Review Scores:**")
            for rv in reviews:
                st.markdown(f"- Score: **{rv.get('score')}/10** | _{rv.get('comments', 'No comments')}_")

        revisions = paper.get('revisions', [])
        if len(revisions) > 1:
            st.markdown(f"**Revision History:** {len(revisions)} version(s)")

        if paper.get('originalHash'):
            st.caption(f"Full hash: `{paper.get('originalHash')}`")

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Connect Wallet")
    wallet = st.text_input("Your Wallet Address", placeholder="0x...", key="wallet_input",
                           help="Enter your Ethereum wallet address to access your role's dashboard")

    role = None
    user_data = None

    if wallet and wallet.startswith("0x") and len(wallet) >= 10:
        with st.spinner("Fetching profile..."):
            data, code = api_get(f"/users/{wallet}")
        if code == 200:
            user_data = data
            role = data.get("role")
            st.success(f"Welcome, **{data.get('name')}**!")
            badge_class = f"badge-{role.lower()}"
            st.markdown(f'<span class="role-badge {badge_class}">{role}</span>', unsafe_allow_html=True)
            st.markdown(f'<div class="sidebar-wallet">{wallet}</div>', unsafe_allow_html=True)
        elif code == 404:
            st.warning("Wallet not registered. Ask an Admin to register you.")
        elif code == 503:
            st.error("⚠️ Backend offline")
        else:
            st.error(data.get("error", "Error fetching profile"))
    else:
        st.info("Enter your wallet address above to log in.")

    st.divider()
    st.markdown("### 🔧 Backend")
    if st.button("Health Check"):
	    try:
		r = requests.get(f"{API_BASE}/health", timeout=5)
		if r.status_code == 200:
		    st.success("Backend is online")
		else:
		    st.error("Backend returned an error")
	    except:
		st.error("Backend is offline")

    st.divider()
    st.caption("Academic Peer Review System")
    st.caption("Blockchain · IPFS · MongoDB")

# ─── MAIN HEADER ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>📚 Academic Peer Review System</h1>
    <p>Transparent · Immutable · Decentralized</p>
</div>
""", unsafe_allow_html=True)

# ─── NOT LOGGED IN ────────────────────────────────────────────────────────────
if not wallet or not wallet.startswith("0x"):
    st.info("Please enter your wallet address in the sidebar to access your dashboard.")
    
    with st.expander("ℹ️ About this system"):
        st.markdown("""
        This system manages the academic peer review lifecycle on a **blockchain ledger**:
        
        | Role | Capabilities |
        |------|-------------|
        | **Admin** | Register users (authors, reviewers, editors) on-chain |
        | **Author** | Submit papers, track review status, submit revisions |
        | **Reviewer** | Evaluate assigned papers, submit scores and comments |
        | **Editor** | Assign reviewers to papers, record final decisions |
        
        Every key event — submission, assignment, review score, final decision — is recorded as an **immutable blockchain transaction**. Reviewer identity is protected through anonymized hash-based identification.
        """)
    st.stop()

elif not role:
    st.warning("Your wallet is not registered in the system. Contact an Admin.")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════
#  ADMIN DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════
if role == "Admin":
    st.subheader(" Admin Dashboard")
    tab1, tab2 = st.tabs(["Register User", "All Users"])

    with tab1:
        st.markdown("### Register a New User On-Chain")
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_wallet  = st.text_input("Wallet Address *", placeholder="0x...")
                new_name    = st.text_input("Full Name *", placeholder="Dr. Jane Smith")
            with col2:
                new_email   = st.text_input("Email *", placeholder="jane@university.edu")
                new_role    = st.selectbox("Role *", ["Author", "Reviewer", "Editor", "Admin"])

            reviewer_id = None
            if new_role == "Reviewer":
                reviewer_id = st.text_input("Reviewer ID *",
                    placeholder="e.g. REV-2024-001  (will be hashed for anonymity)",
                    help="This ID is hashed before being stored on-chain to preserve anonymity.")

            submitted = st.form_submit_button("🔗 Register On-Chain", type="primary", use_container_width=True)
            if submitted:
                if not new_wallet or not new_name or not new_email:
                    st.error("Please fill in all required fields.")
                elif new_role == "Reviewer" and not reviewer_id:
                    st.error("Reviewer ID is required for the Reviewer role.")
                else:
                    payload = {
                        "walletAddress": new_wallet,
                        "name": new_name,
                        "email": new_email,
                        "role": new_role,
                        "reviewerId": reviewer_id
                    }
                    with st.spinner("Registering on blockchain..."):
                        data, code = api_post("/users/register", payload)
                    if code == 201:
                        st.success(f" {new_name} registered as **{new_role}** successfully!")
                        st.info("Transaction has been recorded on the blockchain ledger.")
                    else:
                        st.error(f" {data.get('error', 'Registration failed')}")

    with tab2:
        st.markdown("### All Registered Users")
        if st.button("🔄 Refresh Users"):
            st.cache_data.clear()

        data, code = api_get("/users/all")
        if code == 200:
            users = data.get("users", [])
            if not users:
                st.info("No users registered yet.")
            else:
                role_colors = {"Admin":"🔴","Editor":"🟡","Author":"🟢","Reviewer":"🔵"}
                for u in users:
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                    col1.markdown(f"**{u.get('name')}**")
                    col2.markdown(f"`{u.get('walletAddress','')[:16]}...`")
                    col3.markdown(f"{role_colors.get(u.get('role',''),'⚪')} {u.get('role')}")
                    col4.markdown(f"_{fmt_date(u.get('createdAt',''))}_")
                    st.divider()
        else:
            st.error(data.get("error", "Could not fetch users"))

# ═══════════════════════════════════════════════════════════════════════════
#  AUTHOR DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════
elif role == "Author":
    st.subheader("Author Dashboard")
    tab1, tab2, tab3 = st.tabs(["Submit Paper", "My Papers", "Submit Revision"])

    # ── Submit Paper ────────────────────────────────────────────────────────
    with tab1:
        st.markdown("### Submit a New Paper")
        st.info("Your paper PDF should already be uploaded to IPFS. Provide the CID here.")
        with st.form("submit_paper_form"):
            title    = st.text_input("Paper Title *", placeholder="e.g. Decentralized Identity in Web3")
            abstract = st.text_area("Abstract *", placeholder="Briefly describe your research...", height=120)
            ipfs_cid = st.text_input("IPFS CID *", placeholder="Qm... or bafy...",
                                     help="The IPFS Content Identifier of your uploaded paper PDF.")

            submitted = st.form_submit_button("Submit to Blockchain", type="primary", use_container_width=True)
            if submitted:
                if not title or not abstract or not ipfs_cid:
                    st.error("All fields are required.")
                else:
                    payload = {
                        "title": title,
                        "abstract": abstract,
                        "authorWallet": wallet,
                        "ipfsCID": ipfs_cid
                    }
                    with st.spinner("Submitting paper hash to blockchain..."):
                        data, code = api_post("/papers/submit", payload)
                    if code == 201:
                        st.success("Paper submitted successfully!")
                        col1, col2 = st.columns(2)
                        col1.markdown(f"**Paper Hash:**")
                        col1.markdown(f'<div class="tx-hash">{data.get("paperHash")}</div>', unsafe_allow_html=True)
                        col2.markdown(f"**Tx Hash:**")
                        col2.markdown(f'<div class="tx-hash">{data.get("txHash")}</div>', unsafe_allow_html=True)
                        st.caption("Keep your Paper Hash — you'll need it to track your submission.")
                    else:
                        st.error(f" {data.get('error', 'Submission failed')}")

    # ── My Papers ────────────────────────────────────────────────────────────
    with tab2:
        st.markdown("### My Submitted Papers")
        if st.button("🔄 Refresh", key="refresh_author"):
            pass

        data, code = api_get(f"/papers/author/{wallet}")
        if code == 200:
            papers = data.get("papers", [])
            if not papers:
                st.info("You haven't submitted any papers yet.")
            else:
                # Summary metrics
                statuses = [p.get("status") for p in papers]
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total", len(papers))
                c2.metric("Under Review", statuses.count("Under Review"))
                c3.metric("Accepted", statuses.count("Accepted"))
                c4.metric("Rejected", statuses.count("Rejected"))
                st.divider()
                for p in papers:
                    show_paper_card(p)
        else:
            st.error(data.get("error", "Could not fetch papers"))

    # ── Submit Revision ───────────────────────────────────────────────────────
    with tab3:
        st.markdown("### Submit a Revised Manuscript")
        st.info("Upload your revised PDF to IPFS first, then submit the new CID here. A new revision hash will be linked to the original on-chain.")
        with st.form("revise_form"):
            orig_hash   = st.text_input("Original Paper Hash *", placeholder="0x...")
            new_cid     = st.text_input("New IPFS CID *", placeholder="Qm...",
                                        help="CID of your revised PDF on IPFS.")
            submitted = st.form_submit_button("Submit Revision", type="primary", use_container_width=True)
            if submitted:
                if not orig_hash or not new_cid:
                    st.error("Both fields are required.")
                else:
                    payload = {"originalHash": orig_hash, "newIpfsCID": new_cid, "authorWallet": wallet}
                    with st.spinner("Recording revision on blockchain..."):
                        data, code = api_post("/papers/revise", payload)
                    if code == 200:
                        st.success("Revision submitted! Paper re-enters the review queue.")
                        st.markdown(f"**New Revision Hash:** `{data.get('newRevisionHash')}`")
                        st.markdown(f"**Tx Hash:** `{data.get('txHash')}`")
                    else:
                        st.error(f" {data.get('error', 'Revision failed')}")

# ═══════════════════════════════════════════════════════════════════════════
#  REVIEWER DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════
elif role == "Reviewer":
    st.subheader("Reviewer Dashboard")
    tab1, tab2 = st.tabs(["Assigned Papers", "Submit Review"])

    with tab1:
        st.markdown("### Papers Assigned to You")
        st.caption("Your identity is protected — scores are recorded against your anonymous hash, not your wallet address.")
        if st.button("🔄 Refresh", key="refresh_reviewer"):
            pass

        data, code = api_get(f"/papers/assigned/{wallet}")
        if code == 200:
            papers = data.get("papers", [])
            if not papers:
                st.info("No papers are currently assigned to you.")
            else:
                for p in papers:
                    show_paper_card(p)
        else:
            st.error(data.get("error", "Could not fetch assigned papers"))

    with tab2:
        st.markdown("### Submit a Review Score")
        st.warning("⚠️ Once a final decision is recorded by the Editor, no further reviews are accepted.")
        with st.form("review_form"):
            paper_hash = st.text_input("Paper Hash *", placeholder="0x...",
                                       help="The original hash of the paper assigned to you.")
            score = st.slider("Review Score *", min_value=0, max_value=10, value=7,
                              help="0 = Poor / 10 = Excellent")
            st.markdown(f"**Selected Score: {score}/10**")
            comments = st.text_area("Comments / Feedback", placeholder="Provide detailed feedback for the author and editor...", height=150)

            submitted = st.form_submit_button("Submit Review to Blockchain", type="primary", use_container_width=True)
            if submitted:
                if not paper_hash:
                    st.error("Paper Hash is required.")
                else:
                    payload = {
                        "paperHash": paper_hash,
                        "reviewerWallet": wallet,
                        "score": score,
                        "comments": comments
                    }
                    with st.spinner("Recording review on blockchain..."):
                        data, code = api_post("/papers/review", payload)
                    if code == 200:
                        st.success("Review submitted! Score recorded immutably on-chain.")
                        st.markdown(f"**Tx Hash:** `{data.get('txHash')}`")
                        st.caption("Your identity is preserved — only your anonymous hash was recorded on the ledger.")
                    else:
                        st.error(f" {data.get('error', 'Review submission failed')}")

# ═══════════════════════════════════════════════════════════════════════════
#  EDITOR DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════
elif role == "Editor":
    st.subheader("Editor Dashboard")
    tab1, tab2, tab3 = st.tabs(["All Papers", "Assign Reviewer", "Finalize Decision"])

    with tab1:
        st.markdown("### All Submitted Papers")
        if st.button("Refresh All", key="refresh_editor"):
            pass

        data, code = api_get("/papers")
        if code == 200:
            papers = data.get("papers", [])
            if not papers:
                st.info("No papers in the system yet.")
            else:
                # Status filter
                all_statuses = list(set(p.get("status","") for p in papers))
                selected_status = st.multiselect("Filter by Status", all_statuses, default=all_statuses)
                filtered = [p for p in papers if p.get("status") in selected_status]

                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Total", len(papers))
                c2.metric("Submitted", sum(1 for p in papers if p.get("status")=="Submitted"))
                c3.metric("Under Review", sum(1 for p in papers if p.get("status")=="Under Review"))
                c4.metric("Accepted", sum(1 for p in papers if p.get("status")=="Accepted"))
                c5.metric("Rejected", sum(1 for p in papers if p.get("status")=="Rejected"))
                st.divider()

                for p in filtered:
                    show_paper_card(p)
        else:
            st.error(data.get("error", "Could not fetch papers"))

    with tab2:
        st.markdown("### Assign a Reviewer to a Paper")
        st.info("Reviewers are identified on-chain by their anonymous hash — their wallet address is not exposed.")

        # Load reviewers for dropdown
        rev_data, rev_code = api_get("/users/reviewers")
        reviewers = rev_data.get("reviewers", []) if rev_code == 200 else []

        with st.form("assign_form"):
            paper_hash_assign = st.text_input("Paper Hash *", placeholder="0x...")

            if reviewers:
                rev_options = {f"{r.get('name')} ({r.get('walletAddress','')[:14]}...)": r.get('walletAddress') for r in reviewers}
                selected_rev_label = st.selectbox("Select Reviewer *", list(rev_options.keys()))
                reviewer_wallet = rev_options[selected_rev_label]
                st.caption(f"Wallet: `{reviewer_wallet}`")
            else:
                reviewer_wallet = st.text_input("Reviewer Wallet Address *", placeholder="0x...",
                                                help="No reviewers loaded — enter manually.")

            submitted = st.form_submit_button(" Assign Reviewer On-Chain", type="primary", use_container_width=True)
            if submitted:
                if not paper_hash_assign or not reviewer_wallet:
                    st.error("Both fields are required.")
                else:
                    payload = {"paperHash": paper_hash_assign, "reviewerWallet": reviewer_wallet}
                    with st.spinner("Recording assignment on blockchain..."):
                        data, code = api_post("/papers/assign", payload)
                    if code == 200:
                        st.success("Reviewer assigned! Transaction recorded on-chain.")
                        st.json({"paper_status": data.get("paper", {}).get("status"), "assigned_to": reviewer_wallet})
                    else:
                        st.error(f" {data.get('error', 'Assignment failed')}")

    with tab3:
        st.markdown("### Record Final Editorial Decision")
        st.error("⚠️ **This action is irreversible.** Once a decision is finalized, no further score changes or decision updates are permitted by any wallet.")

        DECISIONS = {
            "Accept": 1,
            "Reject": 2,
            "Request Revision": 3
        }

        with st.form("decision_form"):
            paper_hash_dec = st.text_input("Paper Hash *", placeholder="0x...")
            decision_label = st.radio("Final Decision *", list(DECISIONS.keys()))
            confirm = st.checkbox("I understand this decision is immutable and cannot be reversed.")

            submitted = st.form_submit_button("⚖️ Record Decision On-Chain", type="primary", use_container_width=True)
            if submitted:
                if not paper_hash_dec:
                    st.error("Paper Hash is required.")
                elif not confirm:
                    st.error("Please confirm that you understand this action is irreversible.")
                else:
                    decision_val = DECISIONS[decision_label]
                    payload = {"paperHash": paper_hash_dec, "decision": decision_val}
                    with st.spinner("Writing final decision to blockchain..."):
                        data, code = api_post("/papers/decision", payload)
                    if code == 200:
                        st.success(f" Decision recorded: **{decision_label}**")
                        st.markdown(f"**Tx Hash:** `{data.get('txHash')}`")
                        st.caption("This transaction is now permanently recorded on the immutable ledger.")
                    else:
                        st.error(f" {data.get('error', 'Decision recording failed')}")

# ─── PAPER LOOKUP (AVAILABLE TO ALL ROLES) ───────────────────────────────────
st.divider()
with st.expander("Paper Lookup — Search Any Paper by Hash"):
    lookup_hash = st.text_input("Enter Paper Hash", placeholder="0x...", key="lookup_hash")
    if st.button("Search", key="lookup_btn") and lookup_hash:
        data, code = api_get(f"/papers/{lookup_hash}")
        if code == 200:
            show_paper_card(data, expanded=True)
            if data.get("blockchainState"):
                bs = data["blockchainState"]
                status_names = {0:"Submitted",1:"Assigned",2:"Reviewed",3:"Decision Recorded"}
                decision_names = {0:"Pending",1:"Accepted",2:"Rejected",3:"Revision Required"}
                st.markdown("**On-Chain State:**")
                col1, col2 = st.columns(2)
                col1.info(f"Status: {status_names.get(bs.get('status'), bs.get('status'))}")
                col2.info(f"Decision: {decision_names.get(bs.get('decision'), bs.get('decision'))}")
        elif code == 404:
            st.warning("Paper not found.")
        else:
            st.error(data.get("error", "Error fetching paper"))
