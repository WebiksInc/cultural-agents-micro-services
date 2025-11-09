import sessionManager from './sessionManager';
import logger from '../utils/logger';
import { Api } from 'telegram';

export const votePoll = async (
  phone: string,
  chatId: string,
  messageId: number,
  optionIds: number[]
): Promise<{ pollId: string; messageId: number; votedOptions: number[] }> => {
  const client = sessionManager.getClient(phone);
  
  if (!client) {
    throw new Error(`No authenticated session found for ${phone}`);
  }

  if (!client.connected) {
    await client.connect();
  }

  logger.info('Voting on poll', { phone, chatId, messageId, optionIds });

  try {
    // Force entity resolution - fetch dialogs first to populate cache
    let entity;
    try {
      entity = await client.getEntity(chatId);
    } catch (entityError: unknown) {
      const error = entityError as Error;
      if (error.message.includes('Could not find the input entity')) {
        logger.debug('Entity not in cache, fetching dialogs first', { chatId });
        await client.getDialogs({ limit: 100 });
        entity = await client.getEntity(chatId);
      } else {
        throw entityError;
      }
    }
    
    const messages = await client.getMessages(entity, { ids: [messageId] });
    
    if (!messages || messages.length === 0) {
      throw new Error(`Message not found: ${messageId}`);
    }

    const message = messages[0];
    const media = message.media as Record<string, unknown> | undefined;
    
    if (!media || !media.poll) {
      throw new Error(`Message ${messageId} is not a poll`);
    }

    const poll = media.poll as Record<string, unknown>;
    
    if (poll.closed) {
      throw new Error('This poll is closed and no longer accepts votes');
    }

    const answers = poll.answers as Array<Record<string, unknown>> || [];
    if (optionIds.some(id => id < 0 || id >= answers.length)) {
      throw new Error(`Invalid option ID. Poll has ${answers.length} options (0-${answers.length - 1})`);
    }

    const optionBytes = optionIds.map(id => (answers[id].option as Buffer));

    await client.invoke(
      new Api.messages.SendVote({
        peer: entity,
        msgId: messageId,
        options: optionBytes,
      })
    );

    logger.info('Vote submitted successfully', { phone, chatId, messageId, optionIds });

    return {
      pollId: (poll.id as bigint)?.toString() || String(poll.id),
      messageId,
      votedOptions: optionIds,
    };
  } catch (err: unknown) {
    const error = err as Error;
    logger.error('Failed to vote on poll', { phone, chatId, messageId, error: error.message });
    
    if (error.message.includes('Could not find the input entity')) {
      throw new Error(`Chat not found: ${chatId}`);
    }
    
    throw err;
  }
};

export default {
  votePoll,
};
