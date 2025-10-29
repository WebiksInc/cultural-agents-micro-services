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

export function validateApiCredentials(apiId: any, apiHash: any): { apiId: number; apiHash: string } {
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

export function validateCode(code: any): string {
  if (!code || typeof code !== 'string') {
    throw new Error('Verification code is required');
  }
  
  const cleaned = code.trim();
  
  if (cleaned.length < 5) {
    throw new Error('Verification code is too short');
  }
  
  return cleaned;
}

export function validateMessage(message: any): string {
  if (!message || typeof message !== 'string') {
    throw new Error('Message content is required');
  }
  
  if (message.trim().length === 0) {
    throw new Error('Message cannot be empty');
  }
  
  return message;
}

export function validateTarget(target: any): string {
  if (!target || typeof target !== 'string') {
    throw new Error('Target (phone/username/channel) is required');
  }
  
  const cleaned = target.trim();
  
  if (cleaned.length === 0) {
    throw new Error('Target cannot be empty');
  }
  
  return cleaned;
}

