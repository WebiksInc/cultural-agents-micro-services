import { Router } from 'express';
import authRoutes from './authRoutes';
import messageRoutes from './messageRoutes';
import unreadRoutes from './unreadRoutes';
import chatsRoutes from './chatsRoutes';
import chatMessagesRoutes from './chatMessagesRoutes';
import chatParticipantsRoutes from './chatParticipantsRoutes';
import pollRoutes from './pollRoutes';

const router = Router();

router.use('/auth', authRoutes);
router.use('/messages', messageRoutes);
router.use('/messages', unreadRoutes);
router.use('/chats', chatsRoutes);
router.use('/chat-messages', chatMessagesRoutes);
router.use('/chat-participants', chatParticipantsRoutes);
router.use('/polls', pollRoutes);

export default router;
