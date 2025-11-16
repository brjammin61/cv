import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth/config';
import { prisma } from '@/lib/prisma';
import { sendRealtimeMessage } from '@/lib/pusher/config';

// POST /api/messages - Send a message
export async function POST(req: NextRequest) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { receiverId, content, cardId, transactionId } = await req.json();

    const message = await prisma.message.create({
      data: {
        senderId: session.user.id,
        receiverId,
        content,
        cardId,
        transactionId,
      },
      include: {
        sender: {
          select: {
            id: true,
            name: true,
            image: true,
          },
        },
        receiver: {
          select: {
            id: true,
            name: true,
            image: true,
          },
        },
      },
    });

    // Send real-time notification
    await sendRealtimeMessage(receiverId, message);

    return NextResponse.json(message, { status: 201 });
  } catch (error) {
    console.error('Error sending message:', error);
    return NextResponse.json({ error: 'Failed to send message' }, { status: 500 });
  }
}

// GET /api/messages - Get messages
export async function GET(req: NextRequest) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(req.url);
    const otherUserId = searchParams.get('userId');

    if (otherUserId) {
      // Get conversation with specific user
      const messages = await prisma.message.findMany({
        where: {
          OR: [
            { senderId: session.user.id, receiverId: otherUserId },
            { senderId: otherUserId, receiverId: session.user.id },
          ],
        },
        include: {
          sender: {
            select: {
              id: true,
              name: true,
              image: true,
            },
          },
        },
        orderBy: { createdAt: 'asc' },
      });

      // Mark messages as read
      await prisma.message.updateMany({
        where: {
          senderId: otherUserId,
          receiverId: session.user.id,
          read: false,
        },
        data: {
          read: true,
          readAt: new Date(),
        },
      });

      return NextResponse.json(messages);
    } else {
      // Get all conversations
      const messages = await prisma.message.findMany({
        where: {
          OR: [{ senderId: session.user.id }, { receiverId: session.user.id }],
        },
        include: {
          sender: {
            select: {
              id: true,
              name: true,
              image: true,
            },
          },
          receiver: {
            select: {
              id: true,
              name: true,
              image: true,
            },
          },
        },
        orderBy: { createdAt: 'desc' },
        take: 100,
      });

      return NextResponse.json(messages);
    }
  } catch (error) {
    console.error('Error fetching messages:', error);
    return NextResponse.json({ error: 'Failed to fetch messages' }, { status: 500 });
  }
}
