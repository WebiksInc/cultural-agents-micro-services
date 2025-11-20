import { Router } from 'express';
import authRoutes from './authRoutes';
import messageRoutes from './messageRoutes';
import chatsRoutes from './chatsRoutes';
import chatMessagesRoutes from './chatMessagesRoutes';
import chatParticipantsRoutes from './chatParticipantsRoutes';
import pollRoutes from './pollRoutes';
import typingRoutes from './typingRoutes';

const router = Router();

router.use('/auth', authRoutes);
router.use('/messages', messageRoutes);
router.use('/chats', chatsRoutes);
router.use('/chat-messages', chatMessagesRoutes);
router.use('/participants', chatParticipantsRoutes);
router.use('/polls', pollRoutes);
router.use('/typing', typingRoutes);  

    
export default router;
