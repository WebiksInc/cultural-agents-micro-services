# let's proceed to component  C implenenation.
# i have attached the prompts per trait (OCEAN MODEL, BIG5)
# but note that those prompt were for our evaluation procees so the output structure might be diffrernt here (since we are using state and langgraph).
# here iד the characterization of the component:
# Component C I/O
# Input: recent_messages + target_id (target is the person being analyzed)
# Output: editing the sender_personality field of recent_messages by giving a score from 1 to 5 for each BIG 5 trait (OCEAN model).
#  It has not yet been decided how frequently this component should be executed.
# the pipeline should be a follows:
# the component gets the recent_messages
