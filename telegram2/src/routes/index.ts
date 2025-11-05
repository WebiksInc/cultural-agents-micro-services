import { Router } from 'express';
import authRoutes from './authRoutes';
import messageRoutes from './messageRoutes';
import unreadRoutes from './unreadRoutes';
import chatsRoutes from './chatsRoutes';
import chatMessagesRoutes from './chatMessagesRoutes';

const router = Router();

router.use('/auth', authRoutes);
router.use('/messages', messageRoutes);
router.use('/messages', unreadRoutes);
router.use('/chats', chatsRoutes);
router.use('/chat-messages', chatMessagesRoutes);

export default router;
