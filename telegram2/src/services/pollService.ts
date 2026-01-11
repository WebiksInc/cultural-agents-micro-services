import sessionManager from './sessionManager';
import logger from '../utils/logger';
import entityResolver from './entityResolver';
import { Poll, PollOption } from '../types/polls';

function transformPollOption(option: unknown, results: unknown): PollOption {
  const opt = option as Record<string, unknown>;
  const resultsObj = results as Record<string, unknown>;
  const voters = (resultsObj.results as Array<Record<string, unknown>>) || [];
  
  const optionVoters = voters.find(v => v.option === opt.option);
  const voterCount = (optionVoters?.voters as number) || 0;
  const chosen = (optionVoters?.chosen as boolean) || false;

  return {
    text: opt.text as string,
    voterCount,
    chosen,
  };
}

function transformPoll(message: unknown, _currentUserId: string): Poll | null {
  const msg = message as Record<string, unknown>;
  const media = msg.media as Record<string, unknown> | undefined;
  
  if (!media || !media.poll) {
    return null;
  }

  const poll = media.poll as Record<string, unknown>;
  const results = media.results as Record<string, unknown>;
  const answers = poll.answers as Array<unknown> || [];

  const options = answers.map(opt => 
    transformPollOption(opt, results)
  );

  return {
    messageId: msg.id as number,
    pollId: (poll.id as bigint)?.toString() || String(poll.id),
    question: poll.question as string,
    date: msg.date ? new Date((msg.date as number) * 1000).toISOString() : new Date().toISOString(),
    closed: (poll.closed as boolean) || false,
    multipleChoice: (poll.multipleChoice as boolean) || false,
    quiz: (poll.quiz as boolean) || false,
    options,
    totalVoters: (results.totalVoters as number) || 0,
    closePeriod: poll.closePeriod as number | undefined,
    closeDate: poll.closeDate ? new Date((poll.closeDate as number) * 1000).toISOString() : undefined,
  };
}

export const getPolls = async (
  phone: string,
  chatId: string,
  limit: number
): Promise<{ chatId: string; chatTitle: string; polls: Poll[] }> => {
  const client = sessionManager.getClient(phone);
  
  if (!client) {
    throw new Error(`No authenticated session found for ${phone}`);
  }

  if (!client.connected) {
    logger.debug('Client not connected, attempting to connect', { phone });
    await client.connect();
  }

  logger.info('Fetching polls from chat', { phone, chatId, limit });

  try {
    logger.debug('Resolving entity', { chatId });
    
    const entity = await entityResolver.getEntity(client, phone, chatId);
    
    const messages = await client.getMessages(entity, { limit: limit * 3 });

    const currentUser = await client.getMe();
    const currentUserId = currentUser.id.toString();

    const pollMessages = messages
      .map((msg: unknown) => transformPoll(msg, currentUserId))
      .filter((poll: Poll | null): poll is Poll => poll !== null)
      .slice(0, limit);

    const chatTitle = entity.title || entity.firstName || chatId;

    logger.info('Polls fetched successfully', { 
      phone, 
      chatId, 
      count: pollMessages.length 
    });

    return {
      chatId: entity.id?.toString() || chatId,
      chatTitle,
      polls: pollMessages,
    };
  } catch (err: unknown) {
    const error = err as Error;
    logger.error('Failed to fetch polls', { phone, chatId, error: error.message });
    
    if (error.message.includes('Could not find the input entity')) {
      throw new Error(`Chat not found: ${chatId}`);
    }
    
    throw err;
  }
};

export default {
  getPolls,
};
