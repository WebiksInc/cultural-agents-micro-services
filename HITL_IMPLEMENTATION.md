# Human-in-the-Loop (HITL) Approval System

## Overview

This implementation adds a Human-in-the-Loop approval system to the Cultural Agents project. Before any AI-generated message is sent to Telegram, it can be reviewed and approved by an operator via the Streamlit log-viewer interface.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SUPERVISOR GRAPH FLOW                              │
│                                                                              │
│  START → component_B → component_C → [agents in parallel] →                 │
│  scheduler → human_approval (INTERRUPT) → executor → END                    │
│                    │                                                        │
│                    ▼                                                        │
│          ┌─────────────────────┐      ┌─────────────────────┐              │
│          │  File-Based IPC     │      │  Streamlit UI       │              │
│          │  pending.json       │◄────►│  (Approval Queue)   │              │
│          │  response.json      │      │                     │              │
│          └─────────────────────┘      │  - Auto-refresh     │              │
│                                       │  - Individual       │              │
│                                       │    approve/reject   │              │
│                                       │  - Edit messages    │              │
│                                       └─────────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Configuration

### Enable/Disable HITL

In `langgraph/config/supervisor_config.json`:

```json
{
  "hitl": {
    "enabled": true,
    "description": "Human-in-the-loop approval. Set to false to skip approval and auto-send messages."
  }
}
```

| Setting | Effect |
|---------|--------|
| `"enabled": true` | Messages wait for operator approval in UI |
| `"enabled": false` | Messages auto-approve and send immediately |

---

## Files

### 1. `langgraph/approval_state.py`

File-based IPC for cross-process communication between supervisor and Streamlit.

**Key Components:**
- `ApprovalState` class - File-based state management
- `set_pending()` / `get_pending()` - Store/retrieve pending approvals via `pending.json`
- `set_response()` / `get_response()` - Store/retrieve operator decisions via `response.json`
- `log_rejection()` - Log rejected messages to `rejection_log.json`

**State Files Location:** `langgraph/data/hitl_state/`
- `pending.json` - Supervisor writes, Streamlit reads
- `response.json` - Streamlit writes, Supervisor reads

### 2. `langgraph/nodes/supervisor/human_approval.py`

LangGraph node that implements the interrupt point.

**Key Functions:**
- `is_hitl_enabled()` - Checks config to see if HITL is enabled
- `build_approval_request()` - Builds JSON-serializable payload for UI
- `process_approval_response()` - Processes operator decisions
- `human_approval_node()` - Main node that calls `interrupt()` or auto-approves

### 3. `langgraph/build_graph.py`

**Changes:**
- Added `InMemorySaver` checkpointer import
- Added `human_approval` node between `scheduler` and `executor`
- Updated flow: `scheduler → human_approval → executor`

### 4. `langgraph/run_supervisor.py`

**Changes:**
- Added `invoke_graph_with_hitl()` helper function that:
  - Invokes graph with unique `thread_id` config
  - Detects `__interrupt__` in result
  - Stores pending approval to file
  - Blocks waiting for operator response
  - Resumes graph with `Command(resume=...)`

### 5. `log-viewer/app.py`

**Key Features:**
- Import via `importlib.util` to avoid path conflicts
- Auto-refresh toggle (5-second interval)
- Individual approve/edit/reject buttons per message
- Pending count shown in metrics bar (6th column)
- Better emotion parsing (handles dict/list formats with emoji)
- Sender name fallback chain for context messages

---

## Log Files

### `langgraph/logs/rejection_log.json`

Auto-created when first rejection occurs. Saved immediately on reject.

**Structure:**
```json
[
  {
    "timestamp": "2026-01-12T10:35:00",
    "agent_name": "Chloe",
    "proposed_message": "AI-generated message...",
    "rejection_reason": "Too promotional",
    "replacement_message": "Optional replacement...",
    "trigger_id": "product_mention",
    "action_id": "answer_direct_question",
    "group_id": "3389864729",
    "group_name": "Tech Discussion",
    "context": {
      "action_purpose": "...",
      "trigger_justification": "..."
    }
  }
]
```

---

## How It Works

### Approval Flow (HITL Enabled)

1. **Graph Execution**: Supervisor runs through agents → scheduler
2. **Interrupt**: `human_approval` node calls `interrupt()` with pending messages
3. **File Write**: Approval request saved to `pending.json`
4. **Blocking Wait**: Supervisor polls for `response.json`
5. **Operator Review**: Streamlit UI reads `pending.json` and shows approvals
6. **Decision**: Operator clicks approve/edit/reject per message
7. **File Write**: Decision saved to `response.json`
8. **Resume**: Supervisor reads response and resumes graph
9. **Execution**: `executor` node sends approved messages to Telegram

### Bypass Flow (HITL Disabled)

1. **Graph Execution**: Supervisor runs through agents → scheduler
2. **Auto-Approve**: `human_approval` node skips interrupt, passes actions through
3. **Execution**: `executor` node sends messages immediately

### Operator Actions

| Action | Result |
|--------|--------|
| **Approve** | Message sent as-is |
| **Edit & Approve** | Edited message sent |
| **Reject** | Message logged to rejection_log.json, not sent |
| **Reject + Replace** | Operator's replacement message sent instead |

---

## Usage

### Running the System

1. **Start Streamlit** (in one terminal):
   ```bash
   cd log-viewer
   streamlit run app.py
   ```

2. **Start Supervisor** (in another terminal):
   ```bash
   cd langgraph
   python run_supervisor.py
   ```

3. **When approvals are pending**:
   - The "Approval Queue" tab shows a 🔴 indicator
   - Pending count appears in the metrics bar
   - Review each pending message
   - Click ✅ Approve, ✏️ Edit, or ❌ Reject per message
   - Graph resumes automatically after decision

---

## Configuration Reference

| Setting | Location | Default |
|---------|----------|---------|
| HITL enabled | `config/supervisor_config.json` → `hitl.enabled` | `true` |
| Approval check interval | `run_supervisor.py` | 2 seconds |
| Auto-refresh UI | `app.py` | 5 seconds |
| Max context messages | `app.py` | 15 messages |

---

## Dependencies

No new pip dependencies required. Uses existing:
- `langgraph` (checkpointer, interrupt, Command)
- `streamlit` (UI)
- `json` / `pathlib` (stdlib - file-based IPC)
