"""Example: Agent actions logging."""

from .. import save_action, get_agent_actions, list_agents, get_action_statistics

CHAT_ID = "3389864729"

if __name__ == "__main__":
    # Save some actions
    save_action(
        chat_id=CHAT_ID,
        agent_name="SandraK9",
        group_name="Dev Group",
        trigger_detected="direct_mention",
        triggered_by_msg="@SandraK9 what do you think?",
        action_reason="Direct mention asking for opinion",
        action_id="answer_direct_mention",
        action_content="I think it's great!"
    )
    
    save_action(
        chat_id=CHAT_ID,
        agent_name="Victor",
        group_name="Dev Group",
        trigger_detected="detect_partisan_stance",
        triggered_by_msg="I hate that framework",
        action_reason="Strong partisan stance detected",
        action_id="strawman",
        action_content="So you're against modern development?"
    )
    
    # Get agent's actions
    sandra_actions = get_agent_actions(CHAT_ID, "SandraK9")
    print(f"\nSandraK9 actions: {len(sandra_actions)}")
    for action in sandra_actions:
        print(f"  [{action['timestamp']}] {action['action_id']}")
    
    # List all agents
    agents = list_agents(CHAT_ID)
    print(f"\nAgents: {len(agents)}")
    for agent in agents:
        print(f"  {agent['agent_name']}: {agent['total_actions']} actions")
    
    # Get statistics
    stats = get_action_statistics(CHAT_ID)
    print(f"\nTotal actions: {stats['total_actions']}")
    print(f"Most active: {stats.get('most_active_agent', 'N/A')}")
