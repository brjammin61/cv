import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth/config';
import { prisma } from '@/lib/prisma';
import { sendEmail } from '@/lib/email/send';
import { emailTemplates } from '@/lib/email/templates';
import { sendRealtimeNotification } from '@/lib/pusher/config';

// POST /api/offers - Create an offer
export async function POST(req: NextRequest) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { cardId, amount, message } = await req.json();

    const card = await prisma.card.findUnique({
      where: { id: cardId },
      include: { seller: true },
    });

    if (!card || card.status !== 'ACTIVE') {
      return NextResponse.json({ error: 'Card not available' }, { status: 400 });
    }

    if (card.sellerId === session.user.id) {
      return NextResponse.json({ error: 'Cannot offer on your own card' }, { status: 400 });
    }

    const offer = await prisma.offer.create({
      data: {
        cardId,
        buyerId: session.user.id,
        amount,
        message,
        status: 'PENDING',
      },
      include: {
        card: true,
        buyer: true,
      },
    });

    // Notify seller
    const email = emailTemplates.offerReceived({
      sellerName: card.seller.name || 'there',
      cardTitle: card.title,
      offerAmount: amount,
      buyerName: session.user.name || 'A buyer',
    });

    await Promise.all([
      sendEmail({
        to: card.seller.email!,
        ...email,
      }),
      sendRealtimeNotification(card.sellerId, {
        type: 'NEW_OFFER',
        title: 'New Offer Received',
        message: `${session.user.name} offered $${amount} on ${card.title}`,
        link: `/offers/${offer.id}`,
      }),
    ]);

    return NextResponse.json(offer, { status: 201 });
  } catch (error) {
    console.error('Error creating offer:', error);
    return NextResponse.json({ error: 'Failed to create offer' }, { status: 500 });
  }
}

// GET /api/offers - Get user's offers
export async function GET(req: NextRequest) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(req.url);
    const type = searchParams.get('type'); // 'sent' or 'received'

    const where: any = {};

    if (type === 'sent') {
      where.buyerId = session.user.id;
    } else if (type === 'received') {
      where.card = {
        sellerId: session.user.id,
      };
    }

    const offers = await prisma.offer.findMany({
      where,
      include: {
        card: true,
        buyer: {
          select: {
            id: true,
            name: true,
            image: true,
            rating: true,
          },
        },
      },
      orderBy: { createdAt: 'desc' },
    });

    return NextResponse.json(offers);
  } catch (error) {
    console.error('Error fetching offers:', error);
    return NextResponse.json({ error: 'Failed to fetch offers' }, { status: 500 });
  }
}
