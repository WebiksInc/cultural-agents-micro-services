import { MessageReaction } from '../types/messages';

export function extractDetailedReactions(reactionList: any): MessageReaction[] {
  const reactionsMap = new Map<string, MessageReaction>();
  
  for (const reaction of reactionList.reactions || []) {
    const peerReaction = reaction.reaction;
    let emoji: string;
    
    if (peerReaction?.emoticon) {
      emoji = peerReaction.emoticon;
    } else if (peerReaction?.documentId) {
      emoji = `custom_${peerReaction.documentId}`;
    } else {
      emoji = 'unknown';
    }
    
    if (!reactionsMap.has(emoji)) {
      reactionsMap.set(emoji, {
        emoji,
        count: 0,
        users: [],
      });
    }
    
    const reactionData = reactionsMap.get(emoji)!;
    reactionData.count++;
    
    const peerId = reaction.peerId;
    if (peerId?.userId) {
      const user = reactionList.users?.find((u: any) => 
        u.id?.toString() === peerId.userId?.toString()
      );
      
      if (user) {
        reactionData.users.push({
          userId: user.id?.toString() || 'unknown',
          username: user.username || null,
          firstName: user.firstName || null,
          lastName: user.lastName || null,
        });
      }
    }
  }
  
  return Array.from(reactionsMap.values());
}