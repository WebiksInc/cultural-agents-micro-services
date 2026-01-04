"""
Cultural Agents Log Viewer

A Streamlit app to visualize Logfire logs organized by:
- Supervisor Runs (complete flow from start to response)
- Agents
- Groups

Run with: streamlit run app.py
"""

import streamlit as st
from datetime import date, timedelta
from utils.data_loader import LogDataLoader

# Page config
st.set_page_config(
    page_title="Cultural Agents - Log Viewer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .metric-card h2 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: bold;
    }
    .metric-card p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 0.9rem;
    }
    
    /* Run card */
    .run-card {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        transition: all 0.2s ease;
    }
    .run-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-color: #667eea;
    }
    .run-card.has-response {
        border-left: 4px solid #10b981;
    }
    .run-card.no-response {
        border-left: 4px solid #6b7280;
    }
    
    /* Agent card */
    .agent-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: left;
        border: 1px solid #475569;
        color: #e2e8f0;
    }
    .agent-card h3 {
        margin: 0;
        color: #f1f5f9;
    }
    .agent-card p {
        color: #cbd5e1;
        margin: 5px 0;
    }
    .agent-card strong {
        color: #f1f5f9;
    }
    .agent-card .emoji {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    
    /* Status badges */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 0.2rem;
    }
    .badge-success {
        background: #d1fae5;
        color: #065f46;
    }
    .badge-warning {
        background: #fef3c7;
        color: #92400e;
    }
    .badge-info {
        background: #dbeafe;
        color: #1e40af;
    }
    .badge-error {
        background: #fee2e2;
        color: #991b1b;
    }
    
    /* Timeline */
    .timeline-item {
        display: flex;
        padding: 0.5rem 0;
        border-left: 2px solid #e5e7eb;
        margin-left: 1rem;
        padding-left: 1rem;
    }
    .timeline-item.node-start {
        border-left-color: #3b82f6;
    }
    .timeline-item.node-end {
        border-left-color: #10b981;
    }
    
    /* Prompt/Response boxes */
    .prompt-box {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .response-box {
        background: #ecfdf5;
        border: 1px solid #a7f3d0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    /* Node flow */
    .node-flow {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: 0.5rem 0;
    }
    .node-badge {
        background: #f3f4f6;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        padding: 0.25rem 0.5rem;
        font-size: 0.75rem;
        font-family: monospace;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 1.5rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


def get_loader():
    """Get log data loader (cached in session state)."""
    if "loader" not in st.session_state:
        st.session_state.loader = LogDataLoader()
    return st.session_state.loader


def render_sidebar():
    """Render sidebar with filters."""
    st.sidebar.markdown("## 🤖 Log Viewer")
    st.sidebar.markdown("---")
    
    loader = get_loader()
    available_dates = loader.get_available_dates()
    
    if not available_dates:
        st.sidebar.error("❌ No log files found")
        st.sidebar.info("Check that logs exist in:\n`langgraph/logs/exports/`")
        return None, None
    
    st.sidebar.markdown("### 📅 Select Date Range")
    
    # Quick filters
    col1, col2, col3 = st.sidebar.columns(3)
    with col1:
        if st.button("Today", use_container_width=True):
            st.session_state.start_date = available_dates[0]
            st.session_state.end_date = available_dates[0]
            st.session_state.all_time = False
    with col2:
        if st.button("7 days", use_container_width=True):
            st.session_state.start_date = available_dates[-1] if len(available_dates) >= 7 else available_dates[-1]
            st.session_state.end_date = available_dates[0]
            st.session_state.all_time = False
    with col3:
        if st.button("All Time", use_container_width=True, type="primary" if st.session_state.get("all_time") else "secondary"):
            st.session_state.start_date = available_dates[-1]
            st.session_state.end_date = available_dates[0]
            st.session_state.all_time = True
    
    # Check if "All Time" is selected
    if st.session_state.get("all_time"):
        st.sidebar.success(f"📆 All Time: {available_dates[-1]} → {available_dates[0]}")
        start_date = available_dates[-1]
        end_date = available_dates[0]
    else:
        # Date inputs
        start_date = st.sidebar.date_input(
            "From",
            value=st.session_state.get("start_date", available_dates[0]),
            min_value=available_dates[-1],
            max_value=available_dates[0],
            key="start_picker"
        )
        end_date = st.sidebar.date_input(
            "To",
            value=st.session_state.get("end_date", available_dates[0]),
            min_value=available_dates[-1],
            max_value=available_dates[0],
            key="end_picker"
        )
    
    st.sidebar.markdown("---")
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Data", use_container_width=True, type="primary"):
        if "loader" in st.session_state:
            del st.session_state.loader
        st.rerun()
    
    # File info
    with st.sidebar.expander("📁 Available Log Files"):
        for d in available_dates[:10]:
            st.caption(f"✅ logs_{d.isoformat()}.json")
        if len(available_dates) > 10:
            st.caption(f"... and {len(available_dates) - 10} more")
    
    return start_date, end_date


def render_metrics(loader: LogDataLoader):
    """Render top metrics dashboard."""
    runs = loader.get_runs_summary()
    agents = loader.get_agents_summary()
    groups = loader.get_groups_summary()
    
    runs_with_response = sum(1 for r in runs if r["has_response"])
    total_prompts = sum(r["prompt_count"] for r in runs)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("🚀 Runs", len(runs))
    with col2:
        st.metric("✅ With Response", runs_with_response)
    with col3:
        st.metric("🤖 Agents", len(agents))
    with col4:
        st.metric("👥 Groups", len(groups))
    with col5:
        st.metric("💬 LLM Calls", total_prompts)


def render_run_card(run: dict, loader: LogDataLoader):
    """Render a single run card."""
    # Determine status
    status_class = "has-response" if run["has_response"] else "no-response"
    status_emoji = "✅" if run["has_response"] else "⏸️"
    status_text = "Response Generated" if run["has_response"] else "No Action Taken"
    
    # Format time
    start_time = loader.format_timestamp(run["start_time"])
    
    with st.container():
        # Header row
        col1, col2, col3 = st.columns([3, 2, 1])
        
        with col1:
            st.markdown(f"### {status_emoji} Run #{run['id']} - {start_time}")
        with col2:
            if run["agents"]:
                agents_str = ", ".join(run["agents"])
                st.markdown(f"🤖 **Agents:** {agents_str}")
        with col3:
            st.markdown(f"⏱️ **{run['duration']}**")
        
        # Info row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.caption(f"📋 {run['log_count']} logs")
        with col2:
            st.caption(f"💬 {run['prompt_count']} LLM calls")
        with col3:
            if run["trigger_detected"]:
                st.caption(f"🎯 Trigger: {run['trigger_detected']}")
        with col4:
            if run["action_selected"]:
                st.caption(f"⚡ Action: {run['action_selected']}")
        
        # Response preview
        if run["response_preview"]:
            st.success(f"💬 **Response:** {run['response_preview']}")
        
        # Nodes executed
        if run["nodes_executed"]:
            nodes_html = " → ".join([f"`{n}`" for n in run["nodes_executed"][:8]])
            st.markdown(f"**Flow:** {nodes_html}")
        
        st.markdown("---")


def render_run_detail(run_id: int, loader: LogDataLoader):
    """Render detailed view of a run."""
    run = loader.get_run_detail(run_id)
    if not run:
        st.error("Run not found")
        return
    
    st.markdown(f"## 🔍 Run #{run_id} Details")
    
    # Summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Duration", loader._calculate_duration(run["start_time"], run["end_time"]))
    with col2:
        st.metric("Total Logs", len(run["logs"]))
    with col3:
        st.metric("Agents", len(run["agents"]))
    with col4:
        status = "✅ Yes" if run["has_response"] else "❌ No"
        st.metric("Response Generated", status)
    
    # Tabs for different views
    tab1, tab2 = st.tabs(["🤖 LLM Interactions", "📜 All Logs"])
    
    with tab1:
        interactions = loader.get_llm_interactions(run["logs"])
        if not interactions:
            st.info("No LLM interactions in this run")
        else:
            for interaction in interactions:
                time_str = loader.format_timestamp(interaction["timestamp"])
                agent = interaction.get("agent", "")
                agent_str = f" ({agent})" if agent else ""
                component = interaction.get("component", "unknown")
                model = interaction.get("model", "")
                output = interaction.get("output", {})
                output_type = output.get("type", "") if isinstance(output, dict) else ""
                
                # Choose icon based on component/output type
                icon = "🤖"
                if "component_b" in component.lower() or output_type == "component_b":
                    icon = "📊"
                elif "component_c" in component.lower() or output_type == "component_c":
                    icon = "👥"
                elif "trigger" in component.lower() or output_type == "trigger_analysis":
                    icon = "🎯"
                elif "decision" in component.lower() or output_type == "decision_maker":
                    icon = "⚡"
                elif "E1" in component or "E2" in component or output_type == "response":
                    icon = "💬"
                elif "validator" in component.lower() or output_type == "validator":
                    icon = "✔️"
                elif "scheduler" in component.lower() or output_type == "scheduler":
                    icon = "📅"
                elif "executor" in component.lower() or output_type == "executor":
                    icon = "🚀"
                
                # Display each component call
                with st.expander(f"{icon} {component}{agent_str} @ {time_str}", expanded=False):
                    # Model (only for LLM components)
                    if model:
                        st.caption(f"**Model:** `{model}`")
                    
                    # Input
                    input_text = interaction.get("input")
                    if input_text:
                        st.markdown("**📥 INPUT:**")
                        input_str = str(input_text) if not isinstance(input_text, str) else input_text
                        st.code(input_str[:4000], language=None)
                    
                    # Output
                    st.markdown("**📤 OUTPUT:**")
                    if output and isinstance(output, dict):
                        output_type = output.get("type", "")
                        
                        if output_type == "component_b":
                            st.write(f"**Messages Analyzed:** {output.get('messages_analyzed', 0)}")
                            st.info(f"**Group Sentiment:** {output.get('group_sentiment', 'N/A')}")
                            if output.get("classified_messages"):
                                st.markdown("**Classified Messages:**")
                                for msg in output.get("classified_messages", [])[:5]:
                                    st.caption(f"• [{msg.get('emotion')}] {msg.get('text', '')[:80]}...")
                        
                        elif output_type == "component_c":
                            personas = output.get("personas_selected", [])
                            st.write(f"**Personas Selected:** {len(personas)}")
                            for p in personas:
                                if isinstance(p, dict):
                                    st.caption(f"• {p.get('first_name', p.get('name', str(p)))}")
                                else:
                                    st.caption(f"• {p}")
                        
                        elif output_type == "trigger_analysis":
                            trigger_id = output.get("trigger_id", "")
                            icon_t = "🟢" if trigger_id != "neutral" else "⚪"
                            st.success(f"{icon_t} **Trigger:** `{trigger_id}`")
                            st.write(f"**Justification:** {output.get('justification', 'N/A')}")
                            target = output.get("target_message", {})
                            if target and isinstance(target, dict):
                                st.info(f"**Target:** \"{target.get('text', 'N/A')}\" (from {target.get('sender_name', 'N/A')})")
                        
                        elif output_type == "decision_maker":
                            st.success(f"**Action:** `{output.get('action_id', 'N/A')}`")
                            st.write(f"**Justification:** {output.get('justification', 'N/A')}")
                        
                        elif output_type == "response":
                            styled = output.get("styled_response", "")
                            generated = output.get("generated_response", "")
                            if styled:
                                st.success(f"**Styled Response:** {styled}")
                            if generated and generated != styled:
                                st.info(f"**Generated Response:** {generated}")
                        
                        elif output_type == "validator":
                            if output.get("is_valid"):
                                st.success("✅ Valid")
                            else:
                                st.error("❌ Invalid")
                            st.write(f"**Feedback:** {output.get('feedback', 'N/A')}")
                        
                        elif output_type == "scheduler":
                            queue = output.get("execution_queue", [])
                            st.write(f"**Execution Queue:** {len(queue)} items")
                            for item in queue[:5]:
                                st.caption(f"• {item}")
                        
                        elif output_type == "executor":
                            st.success("✅ Execution completed")
                        
                        else:
                            # Generic output display
                            st.json(output)
                    else:
                        st.caption("No output captured")
    
    with tab2:
        # Show logs in a table-like format
        for log in run["logs"]:
            time_str = loader.format_timestamp(log.get("start_timestamp"))
            message = log.get("message", "")[:150]
            node = log.get("attributes", {}).get("node", "")
            
            col1, col2, col3 = st.columns([1, 1, 4])
            with col1:
                st.caption(time_str)
            with col2:
                st.caption(node)
            with col3:
                st.text(message)


def render_supervisor_runs_tab(loader: LogDataLoader):
    """Render the Supervisor Runs tab."""
    runs = loader.get_runs_summary()
    
    if not runs:
        st.info("📭 No supervisor runs found in the selected date range")
        st.markdown("A supervisor run starts when new messages trigger the graph and ends after the executor node.")
        return
    
    # Stats row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"### Found **{len(runs)}** supervisor runs")
    with col2:
        with_response = sum(1 for r in runs if r["has_response"])
        st.markdown(f"✅ **{with_response}** generated responses")
    with col3:
        no_response = sum(1 for r in runs if not r["has_response"])
        st.markdown(f"⏸️ **{no_response}** no action taken")
    
    st.markdown("---")
    
    # Filter options
    col1, col2 = st.columns([1, 3])
    with col1:
        filter_option = st.selectbox(
            "Filter",
            ["All Runs", "With Response", "No Response"],
            key="run_filter"
        )
    
    # Apply filter
    if filter_option == "With Response":
        runs = [r for r in runs if r["has_response"]]
    elif filter_option == "No Response":
        runs = [r for r in runs if not r["has_response"]]
    
    # Run selector for detail view
    if runs:
        selected_run_id = st.selectbox(
            "Select a run to view details:",
            options=[r["id"] for r in runs],
            format_func=lambda x: f"Run #{x} - {loader.format_timestamp(next(r['start_time'] for r in runs if r['id'] == x))}",
            key="run_selector"
        )
        
        if selected_run_id:
            render_run_detail(selected_run_id, loader)
        
        st.markdown("---")
        st.markdown("### 📋 All Runs Overview")
        
        # List all runs
        for run in runs[:20]:  # Limit to 20
            render_run_card(run, loader)


def render_agents_tab(loader: LogDataLoader):
    """Render the Agents tab with full metadata."""
    agents = loader.get_agents_summary()
    
    if not agents:
        st.info("📭 No agent activity found in the selected date range")
        return
    
    st.markdown(f"### 🤖 {len(agents)} Active Agents")
    st.markdown("---")
    
    # Agent cards in grid
    cols = st.columns(min(len(agents), 3))
    for i, agent in enumerate(agents):
        with cols[i % 3]:
            agent_type = agent.get("agent_type", "")
            agent_type_config = {
                "active": {"emoji": "🟢", "label": "Active Agent", "color": "#4ade80"},
                "chaos": {"emoji": "🔴", "label": "Chaos Agent", "color": "#f87171"},
                "off_radar": {"emoji": "👤", "label": "Off Radar", "color": "#94a3b8"},
            }
            config = agent_type_config.get(agent_type, {"emoji": "🤖", "label": "Unknown", "color": "#94a3b8"})
            
            phone = agent.get("phone_number", "")
            occupation = agent.get("occupation", "")
            nationality = agent.get("nationality", "")
            city = agent.get("city", "")
            
            st.markdown(f"""
            <div class="agent-card" style="border-left: 4px solid {config['color']};">
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <span style="font-size: 2rem; margin-right: 10px;">{config['emoji']}</span>
                    <div>
                        <h3 style="margin: 0;">{agent['name']}</h3>
                        <span style="font-size: 0.8rem; color: {config['color']}; font-weight: bold;">{config['label']}</span>
                    </div>
                </div>
                <p>📞 <strong>{phone if phone else 'No phone'}</strong></p>
                <p>💼 {occupation if occupation else 'N/A'}</p>
                <p>🌍 {f"{city}, {nationality}" if city or nationality else 'N/A'}</p>
                <hr style="margin: 10px 0; border: 0; border-top: 1px solid #475569;">
                <p>📊 <strong>{agent['log_count']}</strong> logs | 🚀 <strong>{agent['runs_participated']}</strong> runs | 💬 <strong>{agent['responses_generated']}</strong> messages</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("")
    
    st.markdown("---")
    
    # Agent detail selector
    selected_agent = st.selectbox(
        "Select an agent to view details:",
        options=[a["name"] for a in agents],
        key="agent_selector"
    )
    
    if selected_agent:
        agent_data = next((a for a in agents if a["name"] == selected_agent), None)
        if agent_data:
            # Agent Info Card
            st.markdown(f"### 🔍 {selected_agent}'s Profile")
            
            # Agent type and goal in a prominent box
            agent_type = agent_data.get("agent_type", "")
            agent_type_config = {
                "active": {"emoji": "🟢", "label": "Active Agent", "color": "#28a745"},
                "chaos": {"emoji": "🔴", "label": "Chaos Agent", "color": "#dc3545"},
                "off_radar": {"emoji": "👤", "label": "Off Radar", "color": "#6c757d"},
            }
            config = agent_type_config.get(agent_type, {"emoji": "🤖", "label": "Unknown", "color": "#6c757d"})
            
            if agent_data.get("agent_goal"):
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, {config['color']}20, {config['color']}10); 
                            border-left: 4px solid {config['color']}; 
                            padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <span style="font-size: 1.5rem; margin-right: 10px;">{config['emoji']}</span>
                        <strong style="color: {config['color']};">{config['label']}</strong>
                    </div>
                    <p style="margin: 0; color: #333;"><strong>🎯 Goal:</strong> {agent_data['agent_goal']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**📋 Identity**")
                st.write(f"**Name:** {agent_data.get('first_name', '')} {agent_data.get('last_name', '')}")
                st.write(f"**Username:** {agent_data.get('user_name', 'N/A')}")
                st.write(f"**Phone:** {agent_data.get('phone_number') or 'N/A'}")
            
            with col2:
                st.markdown("**🌍 Background**")
                st.write(f"**Nationality:** {agent_data.get('nationality', 'N/A')}")
                st.write(f"**City:** {agent_data.get('city', 'N/A')}")
                st.write(f"**Occupation:** {agent_data.get('occupation', 'N/A')}")
            
            with col3:
                st.markdown("**📊 Activity Stats**")
                st.write(f"**Logs:** {agent_data.get('log_count', 0)}")
                st.write(f"**Runs:** {agent_data.get('runs_participated', 0)}")
                st.write(f"**Messages Sent:** {agent_data.get('responses_generated', 0)}")
                st.write(f"**Triggers Detected:** {agent_data.get('triggers_detected', 0)}")
            
            # Style/Persona
            if agent_data.get("style"):
                st.markdown("---")
                st.markdown("**🎭 Persona Style**")
                st.info(agent_data["style"])
            
            # Messages Table - All messages with full metadata
            st.markdown("---")
            st.markdown("### 💬 Messages Sent by Agent")
            
            agent_messages = loader.get_agent_messages(selected_agent)
            
            if agent_messages:
                for msg in agent_messages:
                    with st.container():
                        # Header with date
                        st.markdown(f"#### 📨 Message @ {msg['date']}")
                        
                        # Metadata columns
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Agent Name:** {msg['agent_name']}")
                            st.write(f"**Agent Type:** {msg['agent_type']}")
                            st.write(f"**Phone:** {msg['phone_number'] or 'N/A'}")
                        with col2:
                            st.write(f"**Group:** {msg['group_name'] or 'N/A'}")
                            st.write(f"**Trigger:** `{msg['trigger_id'] or 'N/A'}`")
                            st.write(f"**Action Type:** `{msg['action_type'] or 'N/A'}`")
                        with col3:
                            st.write(f"**Date:** {msg['date']}")
                            if msg.get('target_message'):
                                target = msg['target_message']
                                st.caption(f"In reply to: \"{target.get('text', '')[:50]}...\"")
                        
                        # Message content
                        st.success(f"**Message Content:**\n{msg['message_content']}")
                        
                        # Agent Goal
                        if msg.get('agent_goal'):
                            with st.expander("Agent Goal/Purpose"):
                                st.write(msg['agent_goal'])
                        
                        st.markdown("---")
            else:
                st.info("No messages sent by this agent in the selected period")
            
            # LLM Interactions
            st.markdown("### 🤖 LLM Interactions (Input/Output per Component)")
            
            agent_logs = loader.logs_by_agent.get(selected_agent, [])
            interactions = loader.get_llm_interactions(agent_logs)
            
            if not interactions:
                st.info("No LLM interactions found for this agent")
            else:
                for interaction in interactions[:20]:
                    time_str = loader.format_timestamp(interaction["timestamp"])
                    component = interaction.get("component", "unknown")
                    model = interaction.get("model", "")
                    output = interaction.get("output", {})
                    output_type = output.get("type", "") if isinstance(output, dict) else ""
                    
                    # Choose icon
                    icon = "🤖"
                    if output_type == "trigger_analysis":
                        icon = "🎯"
                    elif output_type == "decision_maker":
                        icon = "⚡"
                    elif output_type == "response":
                        icon = "💬"
                    
                    with st.expander(f"{icon} {component} @ {time_str}"):
                        if model:
                            st.caption(f"**Model:** `{model}`")
                        
                        input_text = interaction.get("input")
                        if input_text:
                            st.markdown("**📥 INPUT:**")
                            input_str = str(input_text) if not isinstance(input_text, str) else input_text
                            st.code(input_str[:3000], language=None)
                        
                        st.markdown("**📤 OUTPUT:**")
                        if output and isinstance(output, dict):
                            output_type = output.get("type", "")
                            
                            if output_type == "trigger_analysis":
                                trigger_id = output.get("trigger_id", "")
                                icon_t = "🟢" if trigger_id != "neutral" else "⚪"
                                st.success(f"{icon_t} **Trigger:** `{trigger_id}`")
                                st.write(f"**Justification:** {output.get('justification', 'N/A')}")
                                target = output.get("target_message", {})
                                if target and isinstance(target, dict):
                                    st.info(f"**Target:** \"{target.get('text', 'N/A')}\"")
                            
                            elif output_type == "decision_maker":
                                st.success(f"**Action:** `{output.get('action_id', 'N/A')}`")
                                st.write(f"**Justification:** {output.get('justification', 'N/A')}")
                            
                            elif output_type == "response":
                                styled = output.get("styled_response", "")
                                generated = output.get("generated_response", "")
                                if styled:
                                    st.success(f"**Response:** {styled}")
                                elif generated:
                                    st.success(f"**Response:** {generated}")
                            
                            elif output_type == "validator":
                                if output.get("is_valid"):
                                    st.success("✅ Valid")
                                else:
                                    st.error("❌ Invalid")
                                st.write(f"**Feedback:** {output.get('feedback', 'N/A')}")
                            
                            else:
                                st.json(output)
                        else:
                            st.caption("No output captured")


def render_groups_tab(loader: LogDataLoader):
    """Render the Groups tab with group-specific data."""
    groups = loader.get_groups_summary()
    
    if not groups:
        st.info("📭 No group activity found in the selected date range")
        return
    
    st.markdown(f"### 👥 {len(groups)} Active Groups")
    st.markdown("---")
    
    # Group selector
    group_names = [f"{g['name']} (ID: {g['id']})" for g in groups]
    selected_group_idx = st.selectbox(
        "Select a group:",
        options=range(len(groups)),
        format_func=lambda x: group_names[x],
        key="group_selector"
    )
    
    if selected_group_idx is not None:
        group = groups[selected_group_idx]
        
        st.markdown(f"## 👥 {group['name']}")
        
        # Group metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Group ID", group["id"])
        with col2:
            st.metric("Supervisor Runs", group["runs_count"])
        with col3:
            st.metric("Responses Sent", group["responses_generated"])
        with col4:
            st.metric("Response Rate", f"{group['response_rate']}%")
        with col5:
            st.metric("Active Agents", len(group["agents_active"]))
        
        if group["topic"]:
            st.info(f"📌 **Topic:** {group['topic']}")
        
        st.markdown("---")
        
        # Active agents in this group
        st.markdown("### 🤖 Agents Active in This Group")
        if group["agents_active"]:
            agent_cols = st.columns(min(len(group["agents_active"]), 4))
            for i, agent_name in enumerate(group["agents_active"]):
                with agent_cols[i % 4]:
                    meta = loader.agent_metadata.get(agent_name, {})
                    agent_type = meta.get("agent_type", "")
                    emoji = {"active": "🟢", "chaos": "🔴", "off_radar": "👤"}.get(agent_type, "🤖")
                    st.markdown(f"{emoji} **{agent_name}**")
                    st.caption(f"Type: {agent_type}")
                    st.caption(f"Phone: {meta.get('phone_number', 'N/A')}")
        else:
            st.caption("No agents found")
        
        st.markdown("---")
        
        # Trigger and Action breakdown
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎯 Triggers in This Group")
            if group["triggers_breakdown"]:
                for trigger_id, count in sorted(group["triggers_breakdown"].items(), key=lambda x: -x[1]):
                    percentage = (count / sum(group["triggers_breakdown"].values())) * 100
                    st.write(f"• `{trigger_id}`: **{count}** ({percentage:.0f}%)")
            else:
                st.caption("No triggers detected")
        
        with col2:
            st.markdown("### ⚡ Actions in This Group")
            if group["actions_breakdown"]:
                for action_id, count in sorted(group["actions_breakdown"].items(), key=lambda x: -x[1]):
                    percentage = (count / sum(group["actions_breakdown"].values())) * 100
                    st.write(f"• `{action_id}`: **{count}** ({percentage:.0f}%)")
            else:
                st.caption("No actions taken")
        
        st.markdown("---")
        
        # Activity dates
        st.markdown("### 📅 Activity Dates")
        dates_str = ", ".join(group["dates_active"])
        st.write(f"Active on: {dates_str}")
        
        st.markdown("---")
        
        # Messages sent in this group
        st.markdown("### 💬 Messages Sent in This Group")
        
        group_messages = loader.get_group_messages(group["id"])
        
        if group_messages:
            for msg in group_messages:
                with st.container():
                    # Header
                    col1, col2, col3 = st.columns([2, 2, 2])
                    with col1:
                        agent_type = msg.get('agent_type', '')
                        emoji = {"active": "🟢", "chaos": "🔴", "off_radar": "👤"}.get(agent_type, "🤖")
                        st.markdown(f"{emoji} **{msg['agent_name']}**")
                        st.caption(f"Type: {agent_type} | Phone: {msg['phone_number'] or 'N/A'}")
                    with col2:
                        st.caption(f"🎯 Trigger: `{msg['trigger_id'] or 'N/A'}`")
                        st.caption(f"⚡ Action: `{msg['action_type'] or 'N/A'}`")
                    with col3:
                        st.caption(f"📅 {msg['date']}")
                        if msg.get('in_reply_to'):
                            st.caption(f"↩️ Reply to: \"{msg['in_reply_to'][:40]}...\"")
                    
                    # Message content
                    st.success(msg['message_content'])
                    st.markdown("---")
        else:
            st.info("No messages sent in this group during the selected period")


def main():
    """Main app entry point."""
    # Sidebar
    start_date, end_date = render_sidebar()
    
    if start_date is None or end_date is None:
        st.warning("⚠️ No log files found. Please check the exports directory.")
        return
    
    # Load data
    loader = get_loader()
    
    with st.spinner("📊 Loading logs..."):
        loader.load_date_range(start_date, end_date)
    
    # Header
    st.title("🤖 Cultural Agents Log Viewer")
    st.caption(f"Viewing logs from {start_date} to {end_date}")
    
    # Top metrics
    render_metrics(loader)
    
    st.markdown("---")
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["🚀 Supervisor Runs", "🤖 Agents", "👥 Groups"])
    
    with tab1:
        render_supervisor_runs_tab(loader)
    
    with tab2:
        render_agents_tab(loader)
    
    with tab3:
        render_groups_tab(loader)


if __name__ == "__main__":
    main()
