import logger from '../utils/logger';

// Cache to track which clients have had their dialogs loaded
const dialogsLoadedCache = new Set<string>();

/**
 * Ensures that the client's entity cache is warmed up by calling getDialogs
 * This is necessary because GramJS's getEntity() requires entities to be in cache
 * when using numeric IDs
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function ensureEntityCacheWarmed(client: any, phone: string): Promise<void> {
  const cacheKey = phone;
  
  if (dialogsLoadedCache.has(cacheKey)) {
    // Cache already warmed for this client
    return;
  }
  
  try {
    logger.debug('Warming entity cache by fetching dialogs', { phone });
    await client.getDialogs({ limit: 100 });
    dialogsLoadedCache.add(cacheKey);
    logger.debug('Entity cache warmed successfully', { phone });
  } catch (err: unknown) {
    const error = err as Error;
    logger.warn('Failed to warm entity cache', { phone, error: error.message });
    // Don't throw - let the actual operation fail with a better error message
  }
}

/**
 * Resolves an entity (chat/user) by ID, username, or phone number
 * Automatically warms the cache if needed
 */
export async function getEntity(
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  client: any,
  phone: string,
  chatId: string
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
): Promise<any> {
  // First, try to get the entity directly
  try {
    return await client.getEntity(chatId);
  } catch (firstError: unknown) {
    const error = firstError as Error;
    
    // If it's a "Could not find the input entity" error and chatId is numeric,
    // warm the cache and try again
    if (error.message.includes('Could not find the input entity')) {
      logger.debug('Entity not in cache, warming cache and retrying', { phone, chatId });
      
      await ensureEntityCacheWarmed(client, phone);
      
      // Try again after warming cache
      try {
        return await client.getEntity(chatId);
      } catch (secondError: unknown) {
        const retryError = secondError as Error;
        logger.error('Entity not found even after cache warm', { 
          phone, 
          chatId, 
          error: retryError.message 
        });
        throw retryError;
      }
    }
    
    // If it's a different error, just throw it
    throw error;
  }
}

/**
 * Clears the cache for a specific phone number
 * Useful when a client disconnects or re-authenticates
 */
export function clearEntityCache(phone: string): void {
  dialogsLoadedCache.delete(phone);
  logger.debug('Entity cache cleared', { phone });
}

/**
 * Clears all entity caches
 */
export function clearAllEntityCaches(): void {
  dialogsLoadedCache.clear();
  logger.debug('All entity caches cleared');
}

export default {
  ensureEntityCacheWarmed,
  getEntity,
  clearEntityCache,
  clearAllEntityCaches,
};
