import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth/config';
import { prisma } from '@/lib/prisma';
import { createEscrowPayment } from '@/lib/stripe/config';
import { sendEmail } from '@/lib/email/send';
import { emailTemplates } from '@/lib/email/templates';
import { sendRealtimeNotification } from '@/lib/pusher/config';

// POST /api/transactions/purchase - Create a purchase
export async function POST(req: NextRequest) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { cardId, authenticationRequired, shippingAddress } = await req.json();

    // Get card and seller
    const card = await prisma.card.findUnique({
      where: { id: cardId },
      include: {
        seller: true,
      },
    });

    if (!card || card.status !== 'ACTIVE') {
      return NextResponse.json({ error: 'Card not available' }, { status: 400 });
    }

    if (card.sellerId === session.user.id) {
      return NextResponse.json({ error: 'Cannot buy your own card' }, { status: 400 });
    }

    if (!card.seller.stripeAccountId) {
      return NextResponse.json(
        { error: 'Seller has not set up payments' },
        { status: 400 }
      );
    }

    // Calculate fees
    const shippingFee = 15;
    const authFee = authenticationRequired ? 150 : 0;
    const platformFee = card.price * 0.05;
    const totalAmount = card.price + shippingFee + authFee;

    // Create Stripe payment intent
    const paymentIntent = await createEscrowPayment({
      amount: totalAmount,
      cardId: card.id,
      buyerId: session.user.id,
      sellerId: card.sellerId,
      sellerStripeAccountId: card.seller.stripeAccountId,
    });

    // Create transaction
    const transaction = await prisma.transaction.create({
      data: {
        cardId: card.id,
        buyerId: session.user.id,
        sellerId: card.sellerId,
        price: card.price,
        platformFee,
        shippingFee,
        authenticationFee: authFee,
        totalAmount,
        authenticationRequired,
        shippingAddress,
        stripePaymentIntentId: paymentIntent.id,
        status: 'PENDING',
        escrowStatus: 'HELD',
      },
      include: {
        card: true,
        buyer: true,
        seller: true,
      },
    });

    // Update card status
    await prisma.card.update({
      where: { id: cardId },
      data: { status: 'PENDING' },
    });

    // Send notifications
    const buyerEmail = emailTemplates.purchaseConfirmation({
      buyerName: session.user.name || 'there',
      cardTitle: card.title,
      amount: totalAmount,
    });

    const sellerEmail = emailTemplates.saleNotification({
      sellerName: card.seller.name || 'there',
      cardTitle: card.title,
      amount: card.price,
      buyerName: session.user.name || 'Buyer',
    });

    await Promise.all([
      sendEmail({
        to: session.user.email!,
        ...buyerEmail,
      }),
      sendEmail({
        to: card.seller.email!,
        ...sellerEmail,
      }),
      sendRealtimeNotification(card.sellerId, {
        type: 'CARD_SOLD',
        title: 'Card Sold!',
        message: `Your ${card.title} has been sold for $${card.price}`,
        link: `/dashboard/transactions/${transaction.id}`,
      }),
    ]);

    return NextResponse.json({
      transaction,
      clientSecret: paymentIntent.client_secret,
    });
  } catch (error) {
    console.error('Error creating purchase:', error);
    return NextResponse.json({ error: 'Failed to create purchase' }, { status: 500 });
  }
}
