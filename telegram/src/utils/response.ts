import { Response } from 'express';

export function sendError(
  res: Response,
  statusCode: number,
  message: string
): void {
  res.status(statusCode).json({
    success: false,
    error: message,
  });
}

export function sendSuccess(
  res: Response,
  data?: any,
  message?: string
): void {
  res.json({
    success: true,
    message,
    data,
  });
}

