import { NextRequest, NextResponse } from 'next/server';
import { headers } from 'next/headers';
import { stripe } from '@/lib/stripe/config';
import { prisma } from '@/lib/prisma';
import Stripe from 'stripe';

// POST /api/webhooks/stripe - Handle Stripe webhooks
export async function POST(req: NextRequest) {
  const body = await req.text();
  const signature = headers().get('stripe-signature')!;

  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(
      body,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET!
    );
  } catch (err: any) {
    console.error('Webhook signature verification failed:', err.message);
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 });
  }

  try {
    switch (event.type) {
      case 'payment_intent.succeeded':
        await handlePaymentSuccess(event.data.object as Stripe.PaymentIntent);
        break;

      case 'payment_intent.payment_failed':
        await handlePaymentFailed(event.data.object as Stripe.PaymentIntent);
        break;

      case 'account.updated':
        await handleAccountUpdated(event.data.object as Stripe.Account);
        break;

      case 'transfer.created':
        await handleTransferCreated(event.data.object as Stripe.Transfer);
        break;

      default:
        console.log(`Unhandled event type: ${event.type}`);
    }

    return NextResponse.json({ received: true });
  } catch (error) {
    console.error('Webhook handler error:', error);
    return NextResponse.json({ error: 'Webhook handler failed' }, { status: 500 });
  }
}

async function handlePaymentSuccess(paymentIntent: Stripe.PaymentIntent) {
  const transaction = await prisma.transaction.findFirst({
    where: { stripePaymentIntentId: paymentIntent.id },
  });

  if (transaction) {
    await prisma.transaction.update({
      where: { id: transaction.id },
      data: {
        status: 'PAID',
        paidAt: new Date(),
      },
    });

    // Mark card as sold
    await prisma.card.update({
      where: { id: transaction.cardId },
      data: { status: 'SOLD' },
    });
  }
}

async function handlePaymentFailed(paymentIntent: Stripe.PaymentIntent) {
  const transaction = await prisma.transaction.findFirst({
    where: { stripePaymentIntentId: paymentIntent.id },
  });

  if (transaction) {
    await prisma.transaction.update({
      where: { id: transaction.id },
      data: {
        status: 'CANCELED',
        canceledAt: new Date(),
      },
    });

    // Make card available again
    await prisma.card.update({
      where: { id: transaction.cardId },
      data: { status: 'ACTIVE' },
    });
  }
}

async function handleAccountUpdated(account: Stripe.Account) {
  if (account.metadata?.userId) {
    await prisma.user.update({
      where: { id: account.metadata.userId },
      data: {
        stripeOnboarded: account.charges_enabled && account.payouts_enabled,
      },
    });
  }
}

async function handleTransferCreated(transfer: Stripe.Transfer) {
  // Log successful transfer
  console.log('Transfer created:', transfer.id);
}
