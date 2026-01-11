"""
Log Data Loader

Loads and parses log export files, providing indexed access by:
- Supervisor runs (from component_b start to executor end)
- Agent name
- Group ID
"""

import json
import re
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict


class LogDataLoader:
    """Load and index log data from export files."""
    
    # Node order in supervisor graph
    SUPERVISOR_NODES = ['component_b', 'component_c', 'scheduler', 'executor']
    AGENT_NODES = ['trigger_analysis', 'decision_maker', 'orchestrator', 'component_E1', 'component_E2', 'validator']
    
    def __init__(self, exports_dir: str = None):
        """Initialize the loader."""
        if exports_dir is None:
            base_path = Path(__file__).parent.parent.parent
            exports_dir = base_path / "langgraph" / "logs" / "exports"
        
        self.exports_dir = Path(exports_dir)
        self.logs: List[Dict] = []
        self.runs: List[Dict] = []  # Supervisor runs
        self.logs_by_agent: Dict[str, List[Dict]] = defaultdict(list)
        self.logs_by_group: Dict[str, Dict] = {}  # group_id -> group_info
        self.agent_metadata: Dict[str, Dict] = {}  # agent_name -> metadata
        self.available_dates: List[date] = []
        
    def get_available_files(self) -> List[Path]:
        """Get list of available log export files."""
        if not self.exports_dir.exists():
            return []
        files = list(self.exports_dir.glob("run_*.json"))
        return sorted(files, reverse=True)
    
    def get_available_dates(self) -> List[date]:
        """Get list of dates with available logs."""
        dates = []
        for f in self.get_available_files():
            try:
                date_str = f.stem.split('_')[1]  # run_YYYY-MM-DD_...
                dates.append(date.fromisoformat(date_str))
            except (ValueError, IndexError):
                continue
        return sorted(set(dates), reverse=True)
    
    def load_date(self, target_date: date) -> Dict:
        """Load logs for a specific date."""
        date_str = target_date.isoformat()
        pattern = f"run_{date_str}_*.json"
        files = list(self.exports_dir.glob(pattern))
        
        if not files:
            return {"logs": [], "export_metadata": {}}
        
        all_logs = []
        latest_metadata = {}
        
        for filepath in files:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_logs.extend(data.get("logs", []))
                # Keep the latest metadata
                if not latest_metadata or data.get("export_metadata", {}).get("exported_at", "") > latest_metadata.get("exported_at", ""):
                    latest_metadata = data.get("export_metadata", {})
        
        return {"logs": all_logs, "export_metadata": latest_metadata}
    
    def load_date_range(self, start_date: date, end_date: date) -> None:
        """Load logs for a date range and build indexes."""
        self.logs = []
        self.runs = []
        self.logs_by_agent = defaultdict(list)
        self.logs_by_group = {}
        self.agent_metadata = {}
        
        current = start_date
        while current <= end_date:
            data = self.load_date(current)
            logs = data.get("logs", [])
            self.logs.extend(logs)
            current = date.fromordinal(current.toordinal() + 1)
        
        # Sort all logs by timestamp (oldest first for run detection)
        self.logs.sort(key=lambda x: x.get("start_timestamp", ""))
        
        # Build indexes
        self._identify_runs()
        self._index_by_agent()
        self._index_by_group()
    
    def _identify_runs(self) -> None:
        """Identify supervisor runs from logs."""
        runs = []
        current_run = None
        
        for log in self.logs:
            message = log.get("message", "")
            timestamp = log.get("start_timestamp", "")
            attrs = log.get("attributes", {})
            
            # Run starts with component_b
            if "▶️ Starting component_b" in message:
                if current_run:
                    # Close previous run
                    current_run["end_time"] = current_run["logs"][-1].get("end_timestamp") if current_run["logs"] else timestamp
                    runs.append(current_run)
                
                current_run = {
                    "id": len(runs) + 1,
                    "start_time": timestamp,
                    "end_time": None,
                    "logs": [log],
                    "agents": set(),
                    "nodes_executed": ["component_b"],
                    "has_response": False,
                    "response_text": None,
                    "trigger_detected": None,
                    "action_selected": None,
                }
            elif current_run:
                current_run["logs"].append(log)
                
                # Track nodes
                node = attrs.get("node") or attrs.get("display_name", "")
                if node and node not in current_run["nodes_executed"]:
                    current_run["nodes_executed"].append(node)
                
                # Track agents
                agent = self._extract_agent_name(log)
                if agent:
                    current_run["agents"].add(agent)
                
                # Detect trigger
                if "detected_trigger" in message or attrs.get("trigger_id"):
                    trigger = attrs.get("trigger_id") or self._extract_from_state(log, "detected_trigger")
                    if trigger:
                        current_run["trigger_detected"] = trigger
                
                # Detect action
                if "selected_action" in message or attrs.get("action_id"):
                    action = attrs.get("action_id") or self._extract_from_state(log, "selected_action")
                    if action:
                        current_run["action_selected"] = action
                
                # Detect response
                state = attrs.get("state", {})
                if isinstance(state, dict):
                    if state.get("styled_response") or state.get("generated_response"):
                        current_run["has_response"] = True
                        current_run["response_text"] = state.get("styled_response") or state.get("generated_response")
                
                # Run ends with executor
                if "executor" in message.lower() or attrs.get("node") == "executor":
                    current_run["end_time"] = log.get("end_timestamp", timestamp)
        
        # Don't forget the last run
        if current_run:
            current_run["end_time"] = current_run["logs"][-1].get("end_timestamp") if current_run["logs"] else current_run["start_time"]
            runs.append(current_run)
        
        # Convert agent sets to lists
        for run in runs:
            run["agents"] = list(run["agents"])
        
        self.runs = runs
    
    def _extract_agent_name(self, log: Dict) -> Optional[str]:
        """Extract agent name from log."""
        attrs = log.get("attributes", {})
        
        # Direct agent_name attribute
        if attrs.get("agent_name"):
            return attrs["agent_name"]
        
        # From display_name like "trigger_analysis (Sandra)"
        display_name = attrs.get("display_name", "")
        match = re.search(r'\(([^)]+)\)', display_name)
        if match:
            return match.group(1)
        
        # From state
        state = attrs.get("state", {})
        if isinstance(state, dict):
            persona = state.get("selected_persona", {})
            if isinstance(persona, dict):
                return persona.get("first_name")
        
        return None
    
    def _extract_from_state(self, log: Dict, key: str) -> Optional[Any]:
        """Extract a value from state in log."""
        attrs = log.get("attributes", {})
        state = attrs.get("state", {})
        if isinstance(state, dict):
            value = state.get(key)
            if isinstance(value, dict):
                return value.get("id") or value
            return value
        return None
    
    def _index_by_agent(self) -> None:
        """Index logs by agent name with full metadata."""
        self.agent_metadata: Dict[str, Dict] = {}  # Store agent metadata
        
        for log in self.logs:
            agent = self._extract_agent_name(log)
            if agent:
                self.logs_by_agent[agent].append(log)
                
                # Extract metadata from state - keep looking until we find complete data
                attrs = log.get("attributes", {})
                state = attrs.get("state", {})
                
                if isinstance(state, dict):
                    persona = state.get("selected_persona", {})
                    
                    # Only update if we found persona with phone_number (complete metadata)
                    if isinstance(persona, dict) and persona.get("phone_number"):
                        # Check if we already have complete metadata
                        existing = self.agent_metadata.get(agent, {})
                        if not existing.get("phone_number"):
                            self.agent_metadata[agent] = {
                                "first_name": persona.get("first_name", agent.split()[0] if agent else ""),
                                "last_name": persona.get("last_name", agent.split()[-1] if agent and " " in agent else ""),
                                "phone_number": persona.get("phone_number", ""),
                                "user_name": persona.get("user_name", ""),
                                "nationality": persona.get("nationality", ""),
                                "city": persona.get("city", ""),
                                "occupation": persona.get("occupation", ""),
                                "style": persona.get("style", ""),
                                "agent_type": state.get("agent_type", ""),
                                "agent_goal": state.get("agent_goal", ""),
                            }
    
    def _index_by_group(self) -> None:
        """Index logs by group."""
        for log in self.logs:
            attrs = log.get("attributes", {})
            
            # Check supervisor_state or state for group_metadata
            for state_key in ["supervisor_state", "state"]:
                state = attrs.get(state_key, {})
                if isinstance(state, dict):
                    group_meta = state.get("group_metadata", {})
                    if isinstance(group_meta, dict) and group_meta.get("id"):
                        group_id = str(group_meta["id"])
                        if group_id not in self.logs_by_group:
                            self.logs_by_group[group_id] = {
                                "id": group_id,
                                "name": group_meta.get("name", f"Group {group_id}"),
                                "topic": group_meta.get("topic", ""),
                                "logs": [],
                                "runs": set(),
                            }
                        self.logs_by_group[group_id]["logs"].append(log)
                        
                        # Find which run this log belongs to
                        for i, run in enumerate(self.runs):
                            if log in run["logs"]:
                                self.logs_by_group[group_id]["runs"].add(i)
                        break
    
    def get_runs_summary(self) -> List[Dict]:
        """Get summary of all supervisor runs."""
        summaries = []
        for run in self.runs:
            duration = self._calculate_duration(run["start_time"], run["end_time"])
            
            # Count prompts and errors
            prompt_count = sum(1 for l in run["logs"] if "📝 Prompt" in l.get("message", ""))
            error_count = sum(1 for l in run["logs"] if l.get("level", 0) >= 40)
            
            summaries.append({
                "id": run["id"],
                "start_time": run["start_time"],
                "end_time": run["end_time"],
                "duration": duration,
                "log_count": len(run["logs"]),
                "agents": run["agents"],
                "nodes_executed": run["nodes_executed"],
                "has_response": run["has_response"],
                "response_preview": (run["response_text"][:100] + "...") if run["response_text"] and len(run["response_text"]) > 100 else run["response_text"],
                "trigger_detected": run["trigger_detected"],
                "action_selected": run["action_selected"],
                "prompt_count": prompt_count,
                "error_count": error_count,
            })
        
        # Sort by start time descending (most recent first)
        summaries.sort(key=lambda x: x["start_time"] or "", reverse=True)
        return summaries
    
    def get_run_detail(self, run_id: int) -> Optional[Dict]:
        """Get detailed information for a specific run."""
        for run in self.runs:
            if run["id"] == run_id:
                return run
        return None
    
    def get_agents_summary(self) -> List[Dict]:
        """Get summary of all agents with full metadata."""
        summaries = []
        for agent_name, logs in self.logs_by_agent.items():
            # Get metadata
            meta = self.agent_metadata.get(agent_name, {})
            
            # Count responses
            response_count = 0
            triggers_detected = []
            actions_taken = []
            messages_sent = []
            groups_active = set()
            dates_active = set()
            
            for log in logs:
                attrs = log.get("attributes", {})
                state = attrs.get("state", {})
                timestamp = log.get("start_timestamp", "")
                
                # Track dates
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        dates_active.add(dt.date().isoformat())
                    except:
                        pass
                
                # Track groups
                group_meta = state.get("group_metadata", {}) if isinstance(state, dict) else {}
                if isinstance(group_meta, dict) and group_meta.get("name"):
                    groups_active.add(group_meta.get("name"))
                
                # Track responses
                if isinstance(state, dict):
                    if state.get("generated_response"):
                        response_count += 1
                        messages_sent.append({
                            "timestamp": timestamp,
                            "text": state.get("styled_response") or state.get("generated_response"),
                        })
                    
                    # Track triggers
                    detected_trigger = state.get("detected_trigger", {})
                    if isinstance(detected_trigger, dict) and detected_trigger.get("id"):
                        triggers_detected.append({
                            "trigger_id": detected_trigger.get("id"),
                            "target_message": detected_trigger.get("target_message", {}),
                            "timestamp": timestamp,
                        })
                    
                    # Track actions
                    selected_action = state.get("selected_action")
                    if isinstance(selected_action, dict) and selected_action.get("id"):
                        actions_taken.append({
                            "action_id": selected_action.get("id"),
                            "timestamp": timestamp,
                        })
            
            # Find runs this agent participated in
            runs_participated = set()
            for i, run in enumerate(self.runs):
                if agent_name in run["agents"]:
                    runs_participated.add(i)
            
            summaries.append({
                "name": agent_name,
                "first_name": meta.get("first_name", agent_name),
                "last_name": meta.get("last_name", ""),
                "phone_number": meta.get("phone_number", ""),
                "user_name": meta.get("user_name", ""),
                "nationality": meta.get("nationality", ""),
                "city": meta.get("city", ""),
                "occupation": meta.get("occupation", ""),
                "style": meta.get("style", ""),
                "agent_type": meta.get("agent_type", ""),
                "agent_goal": meta.get("agent_goal", ""),
                "log_count": len(logs),
                "runs_participated": len(runs_participated),
                "triggers_detected": len(triggers_detected),
                "triggers_list": triggers_detected[-10:],  # Last 10
                "actions_taken": len(actions_taken),
                "actions_list": actions_taken[-10:],  # Last 10
                "responses_generated": response_count,
                "messages_sent": messages_sent[-10:],  # Last 10
                "groups_active": list(groups_active),
                "dates_active": sorted(dates_active, reverse=True),
            })
        
        summaries.sort(key=lambda x: x["log_count"], reverse=True)
        return summaries
    
    def get_groups_summary(self) -> List[Dict]:
        """Get summary of all groups with analytics."""
        summaries = []
        for group_id, group_info in self.logs_by_group.items():
            # Collect analytics
            agents_active = set()
            triggers_by_type = defaultdict(int)
            actions_by_type = defaultdict(int)
            responses_generated = 0
            dates_active = set()
            
            for log in group_info["logs"]:
                attrs = log.get("attributes", {})
                state = attrs.get("state", {})
                timestamp = log.get("start_timestamp", "")
                
                # Track dates
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        dates_active.add(dt.date().isoformat())
                    except:
                        pass
                
                # Track agents
                agent = self._extract_agent_name(log)
                if agent:
                    agents_active.add(agent)
                
                if isinstance(state, dict):
                    # Track triggers
                    detected_trigger = state.get("detected_trigger", {})
                    if isinstance(detected_trigger, dict) and detected_trigger.get("id"):
                        triggers_by_type[detected_trigger.get("id")] += 1
                    
                    # Track actions
                    selected_action = state.get("selected_action")
                    if isinstance(selected_action, dict) and selected_action.get("id"):
                        actions_by_type[selected_action.get("id")] += 1
                    
                    # Track responses
                    if state.get("generated_response"):
                        responses_generated += 1
            
            # Calculate response rate
            total_runs = len(group_info["runs"])
            response_rate = (responses_generated / total_runs * 100) if total_runs > 0 else 0
            
            summaries.append({
                "id": group_id,
                "name": group_info["name"],
                "topic": group_info["topic"],
                "log_count": len(group_info["logs"]),
                "runs_count": total_runs,
                "agents_active": sorted(agents_active),
                "responses_generated": responses_generated,
                "response_rate": round(response_rate, 1),
                "triggers_breakdown": dict(triggers_by_type),
                "actions_breakdown": dict(actions_by_type),
                "dates_active": sorted(dates_active, reverse=True),
                "most_common_trigger": max(triggers_by_type.items(), key=lambda x: x[1])[0] if triggers_by_type else None,
                "most_common_action": max(actions_by_type.items(), key=lambda x: x[1])[0] if actions_by_type else None,
            })
        
        summaries.sort(key=lambda x: x["log_count"], reverse=True)
        return summaries
    
    def get_llm_interactions(self, logs: List[Dict]) -> List[Dict]:
        """Extract LLM prompts and their outputs from logs."""
        interactions = []
        seen_keys = set()  # Avoid duplicates
        
        for log in logs:
            message = log.get("message", "")
            attrs = log.get("attributes", {})
            timestamp = log.get("start_timestamp", "")
            
            # Skip non-relevant logs
            if not ("📝 Prompt" in message or "✅ Output from" in message):
                continue
            
            component = attrs.get("component", attrs.get("node", attrs.get("display_name", "").split(" ")[0] if attrs.get("display_name") else "unknown"))
            agent = self._extract_agent_name(log) or attrs.get("agent_name", "")
            
            # Create unique key to avoid duplicates
            key = (component, agent, timestamp[:19] if timestamp else "")
            if key in seen_keys:
                continue
            seen_keys.add(key)
            
            interaction = {
                "type": "llm_call",
                "timestamp": timestamp,
                "component": component,
                "agent": agent,
                "model": attrs.get("model", ""),
                "input": None,
                "output": None,
            }
            
            # Handle Prompt logs
            if "📝 Prompt" in message:
                interaction["input"] = attrs.get("prompt", attrs.get("user_prompt", ""))
                interaction["model"] = attrs.get("model", "")
            
            # Handle Output logs
            if "✅ Output from" in message:
                # Build output based on what's available
                output_data = {}
                
                # component_b output
                if attrs.get("classified_messages") or attrs.get("group_sentiment"):
                    output_data = {
                        "type": "component_b",
                        "messages_analyzed": attrs.get("messages_analyzed", 0),
                        "group_sentiment": attrs.get("group_sentiment", ""),
                        "classified_messages": attrs.get("classified_messages", []),
                    }
                # component_c output
                elif attrs.get("selected_personas") or attrs.get("personas_selected"):
                    output_data = {
                        "type": "component_c",
                        "personas_selected": attrs.get("selected_personas", attrs.get("personas_selected", [])),
                    }
                # trigger_analysis output
                elif attrs.get("trigger_id"):
                    output_data = {
                        "type": "trigger_analysis",
                        "trigger_id": attrs.get("trigger_id"),
                        "justification": attrs.get("justification", ""),
                        "target_message": attrs.get("target_message", {}),
                    }
                # decision_maker output
                elif attrs.get("action_id"):
                    output_data = {
                        "type": "decision_maker",
                        "action_id": attrs.get("action_id"),
                        "justification": attrs.get("justification", ""),
                    }
                # component_E1/E2 output (response generation)
                elif attrs.get("generated_response") or attrs.get("styled_response"):
                    output_data = {
                        "type": "response",
                        "generated_response": attrs.get("generated_response", ""),
                        "styled_response": attrs.get("styled_response", ""),
                    }
                # validator output
                elif attrs.get("is_valid") is not None:
                    output_data = {
                        "type": "validator",
                        "is_valid": attrs.get("is_valid"),
                        "feedback": attrs.get("feedback", ""),
                    }
                # scheduler output
                elif attrs.get("execution_queue") is not None or "scheduler" in component.lower():
                    output_data = {
                        "type": "scheduler",
                        "execution_queue": attrs.get("execution_queue", []),
                    }
                # executor output  
                elif "executor" in component.lower():
                    output_data = {
                        "type": "executor",
                        "executed": True,
                    }
                else:
                    # Generic output - just capture all relevant attrs
                    output_data = {k: v for k, v in attrs.items() if not k.startswith("code.") and not k.startswith("logfire.")}
                
                interaction["output"] = output_data
            
            interactions.append(interaction)
        
        # Sort by timestamp
        interactions.sort(key=lambda x: x.get("timestamp", ""))
        
        # Now try to merge prompts with their outputs (same component, same agent, close timestamps)
        merged = []
        used_indices = set()
        
        for i, inter in enumerate(interactions):
            if i in used_indices:
                continue
                
            if inter.get("input") and not inter.get("output"):
                # This is a prompt, look for matching output
                for j, other in enumerate(interactions):
                    if j <= i or j in used_indices:
                        continue
                    if other.get("output") and not other.get("input"):
                        # Check if same component and agent
                        if inter["component"] == other["component"] and inter["agent"] == other["agent"]:
                            # Merge
                            inter["output"] = other["output"]
                            used_indices.add(j)
                            break
            
            merged.append(inter)
            used_indices.add(i)
        
        return merged
    
    def get_agent_messages(self, agent_name: str) -> List[Dict]:
        """Get all messages sent by an agent with full metadata."""
        messages = []
        seen_messages = set()  # Deduplicate by message content
        agent_logs = self.logs_by_agent.get(agent_name, [])
        meta = self.agent_metadata.get(agent_name, {})
        
        for log in agent_logs:
            attrs = log.get("attributes", {})
            state = attrs.get("state", {})
            timestamp = log.get("start_timestamp", "")
            
            if not isinstance(state, dict):
                continue
                
            # Check if this log has a generated response (meaning agent sent a message)
            generated_response = state.get("generated_response")
            styled_response = state.get("styled_response")
            
            if generated_response or styled_response:
                # Get group info
                group_meta = state.get("group_metadata", {})
                group_name = group_meta.get("name", "") if isinstance(group_meta, dict) else ""
                
                # Get trigger info
                detected_trigger = state.get("detected_trigger", {})
                trigger_id = detected_trigger.get("id", "") if isinstance(detected_trigger, dict) else ""
                target_message = detected_trigger.get("target_message", {}) if isinstance(detected_trigger, dict) else {}
                
                # Get action info
                selected_action = state.get("selected_action", {})
                action_id = selected_action.get("id", "") if isinstance(selected_action, dict) else ""
                
                # Format date
                date_str = ""
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        date_str = timestamp[:19]
                
                # Deduplicate by message content
                msg_content = styled_response or generated_response
                if msg_content in seen_messages:
                    continue
                seen_messages.add(msg_content)
                
                messages.append({
                    "timestamp": timestamp,
                    "date": date_str,
                    "agent_name": agent_name,
                    "agent_type": meta.get("agent_type", state.get("agent_type", "")),
                    "agent_goal": meta.get("agent_goal", state.get("agent_goal", "")),
                    "phone_number": meta.get("phone_number", ""),
                    "group_name": group_name,
                    "message_content": msg_content,
                    "action_type": action_id,
                    "trigger_id": trigger_id,
                    "target_message": target_message,
                })
        
        # Sort by timestamp descending
        messages.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return messages
    
    def get_group_messages(self, group_id: str) -> List[Dict]:
        """Get all messages and activity for a specific group."""
        group_info = self.logs_by_group.get(group_id, {})
        if not group_info:
            return []
        
        messages = []
        for log in group_info.get("logs", []):
            attrs = log.get("attributes", {})
            state = attrs.get("state", {})
            timestamp = log.get("start_timestamp", "")
            
            if not isinstance(state, dict):
                continue
            
            # Get agent messages in this group
            generated_response = state.get("generated_response")
            styled_response = state.get("styled_response")
            
            if generated_response or styled_response:
                agent_name = self._extract_agent_name(log) or ""
                meta = self.agent_metadata.get(agent_name, {})
                
                detected_trigger = state.get("detected_trigger", {})
                trigger_id = detected_trigger.get("id", "") if isinstance(detected_trigger, dict) else ""
                target_message = detected_trigger.get("target_message", {}) if isinstance(detected_trigger, dict) else {}
                
                selected_action = state.get("selected_action", {})
                action_id = selected_action.get("id", "") if isinstance(selected_action, dict) else ""
                
                date_str = ""
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        date_str = timestamp[:19]
                
                messages.append({
                    "timestamp": timestamp,
                    "date": date_str,
                    "agent_name": agent_name,
                    "agent_type": meta.get("agent_type", state.get("agent_type", "")),
                    "phone_number": meta.get("phone_number", ""),
                    "message_content": styled_response or generated_response,
                    "action_type": action_id,
                    "trigger_id": trigger_id,
                    "target_message": target_message,
                    "in_reply_to": target_message.get("text", "") if target_message else "",
                })
        
        messages.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return messages
    
    def _calculate_duration(self, start: str, end: str) -> str:
        """Calculate duration between timestamps."""
        if not start or not end:
            return "N/A"
        try:
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
            delta = end_dt - start_dt
            seconds = delta.total_seconds()
            if seconds < 0:
                return "N/A"
            if seconds < 60:
                return f"{seconds:.1f}s"
            elif seconds < 3600:
                return f"{seconds/60:.1f}m"
            else:
                return f"{seconds/3600:.1f}h"
        except:
            return "N/A"
    
    def format_timestamp(self, ts: str, include_date: bool = True) -> str:
        """Format timestamp for display."""
        if not ts:
            return ""
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if include_date:
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            return dt.strftime("%H:%M:%S")
        except:
            return ts[:19] if ts else ""
