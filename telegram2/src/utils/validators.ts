export function validatePhone(phone: any): string {
  if (!phone || typeof phone !== 'string') {
    throw new Error('Phone number is required and must be a string');
  }
  
  const cleaned = phone.trim();
  
  if (!cleaned.startsWith('+')) {
    throw new Error('Phone number must start with +');
  }
  
  if (cleaned.length < 10) {
    throw new Error('Phone number is too short');
  }
  
  return cleaned;
}

export const validateApiCredentials = (apiId: any, apiHash: any): { apiId: number; apiHash: string } => {
  if (!apiId) {
    throw new Error('apiId is required');
  }
  
  if (!apiHash || typeof apiHash !== 'string') {
    throw new Error('apiHash is required and must be a string');
  }
  
  const id = Number(apiId);
  
  if (isNaN(id) || id <= 0) {
    throw new Error('apiId must be a positive number');
  }
  
  return { apiId: id, apiHash: apiHash.trim() };
}

export const validateCode = (code: any): string => {
  if (!code || typeof code !== 'string') {
    throw new Error('Verification code is required');
  }
  
  const cleaned = code.trim();
  
  if (cleaned.length < 5) {
    throw new Error('Verification code is too short');
  }
  
  return cleaned;
}

export const validateMessage = (message: any): string => {
  if (!message || typeof message !== 'string') {
    throw new Error('Message content is required');
  }
  
  if (message.trim().length === 0) {
    throw new Error('Message cannot be empty');
  }
  
  return message;
}

export const validateTarget = (target: any): string => {
  if (!target || typeof target !== 'string') {
    throw new Error('Target (phone/username/channel) is required');
  }
  
  const cleaned = target.trim();
  
  if (cleaned.length === 0) {
    throw new Error('Target cannot be empty');
  }
  
  return cleaned;
}

export const validateContent = (content: any): { type: 'text' | 'emoji'; value: string } => {
  if (!content || typeof content !== 'object') {
    throw new Error('Content is required and must be an object');
  }

  const { type, value } = content;

  if (!type || (type !== 'text' && type !== 'emoji')) {
    throw new Error('Content type must be either "text" or "emoji"');
  }

  if (!value || typeof value !== 'string') {
    throw new Error('Content value is required and must be a string');
  }

  const cleanedValue = value.trim();

  if (cleanedValue.length === 0) {
    throw new Error('Content value cannot be empty');
  }

  return { type, value: cleanedValue };
}

export const validateReplyTo = (replyTo: any): number | undefined => {
  if (replyTo === undefined || replyTo === null) {
    return undefined;
  }

  const messageId = Number(replyTo);

  if (isNaN(messageId) || messageId <= 0) {
    throw new Error('replyTo must be a positive number');
  }

  return messageId;
}


export default {
  validatePhone,
  validateApiCredentials,
  validateCode,
  validateMessage,
  validateTarget,
  validateContent,
  validateReplyTo
};
