import Stripe from 'stripe';

if (!process.env.STRIPE_SECRET_KEY) {
  throw new Error('STRIPE_SECRET_KEY is not defined');
}

export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY, {
  apiVersion: '2024-11-20.acacia',
  typescript: true,
});

export const PLATFORM_FEE_PERCENT = parseFloat(
  process.env.STRIPE_PLATFORM_FEE_PERCENT || '5'
);

// Create Stripe Connect account for sellers
export async function createConnectAccount(userId: string, email: string) {
  const account = await stripe.accounts.create({
    type: 'express',
    email,
    capabilities: {
      card_payments: { requested: true },
      transfers: { requested: true },
    },
    metadata: {
      userId,
    },
  });

  return account;
}

// Create account link for onboarding
export async function createAccountLink(accountId: string) {
  const accountLink = await stripe.accountLinks.create({
    account: accountId,
    refresh_url: `${process.env.NEXT_PUBLIC_APP_URL}/seller/onboarding`,
    return_url: `${process.env.NEXT_PUBLIC_APP_URL}/seller/dashboard`,
    type: 'account_onboarding',
  });

  return accountLink.url;
}

// Create payment intent with escrow (hold funds)
export async function createEscrowPayment({
  amount,
  cardId,
  buyerId,
  sellerId,
  sellerStripeAccountId,
}: {
  amount: number;
  cardId: string;
  buyerId: string;
  sellerId: string;
  sellerStripeAccountId: string;
}) {
  const platformFee = Math.round(amount * (PLATFORM_FEE_PERCENT / 100));
  const sellerAmount = amount - platformFee;

  const paymentIntent = await stripe.paymentIntents.create({
    amount: Math.round(amount * 100), // Convert to cents
    currency: 'usd',
    payment_method_types: ['card'],
    capture_method: 'manual', // Hold the funds
    metadata: {
      cardId,
      buyerId,
      sellerId,
    },
    transfer_data: {
      destination: sellerStripeAccountId,
    },
    application_fee_amount: platformFee * 100,
  });

  return paymentIntent;
}

// Capture escrowed payment (release to seller)
export async function captureEscrowPayment(paymentIntentId: string) {
  const paymentIntent = await stripe.paymentIntents.capture(paymentIntentId);
  return paymentIntent;
}

// Refund escrowed payment (return to buyer)
export async function refundEscrowPayment(paymentIntentId: string) {
  const refund = await stripe.refunds.create({
    payment_intent: paymentIntentId,
  });
  return refund;
}

// Get account status
export async function getAccountStatus(accountId: string) {
  const account = await stripe.accounts.retrieve(accountId);
  return {
    charges_enabled: account.charges_enabled,
    payouts_enabled: account.payouts_enabled,
    details_submitted: account.details_submitted,
  };
}
