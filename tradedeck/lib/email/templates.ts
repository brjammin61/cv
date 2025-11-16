export const emailTemplates = {
  welcomeEmail: (name: string) => ({
    subject: 'Welcome to TradeDeck! 🎴',
    html: `
      <!DOCTYPE html>
      <html>
        <head>
          <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #0ea5e9 0%, #d946ef 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
            .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
            .button { background: #0ea5e9; color: white; padding: 12px 30px; text-decoration: none; border-radius: 25px; display: inline-block; margin: 20px 0; }
            .footer { text-align: center; margin-top: 30px; color: #666; font-size: 12px; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>🎴 Welcome to TradeDeck!</h1>
            </div>
            <div class="content">
              <h2>Hi ${name},</h2>
              <p>Welcome to the future of trading card collecting! We're thrilled to have you join our community.</p>

              <h3>🚀 Get Started:</h3>
              <ul>
                <li>✨ Swipe to discover amazing cards</li>
                <li>💰 Buy securely with escrow protection</li>
                <li>📦 Sell your collection with just 5% fees</li>
                <li>🛡️ Protected by our guarantee</li>
              </ul>

              <a href="${process.env.NEXT_PUBLIC_APP_URL}/discover" class="button">Start Swiping</a>

              <p>Have questions? Just reply to this email - we're here to help!</p>

              <p>Happy collecting,<br>The TradeDeck Team</p>
            </div>
            <div class="footer">
              <p>&copy; 2024 TradeDeck. All rights reserved.</p>
            </div>
          </div>
        </body>
      </html>
    `,
  }),

  purchaseConfirmation: (details: {
    buyerName: string;
    cardTitle: string;
    amount: number;
    trackingNumber?: string;
  }) => ({
    subject: `Purchase Confirmed: ${details.cardTitle}`,
    html: `
      <!DOCTYPE html>
      <html>
        <body>
          <div class="container">
            <div class="header">
              <h1>✅ Purchase Confirmed!</h1>
            </div>
            <div class="content">
              <h2>Hi ${details.buyerName},</h2>
              <p>Your purchase has been confirmed and your payment is securely held in escrow.</p>

              <div style="background: white; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h3>${details.cardTitle}</h3>
                <p><strong>Amount:</strong> $${details.amount.toLocaleString()}</p>
                ${
                  details.trackingNumber
                    ? `<p><strong>Tracking:</strong> ${details.trackingNumber}</p>`
                    : ''
                }
              </div>

              <p>🛡️ <strong>You're Protected:</strong> Your payment is held securely until delivery is confirmed.</p>

              <a href="${process.env.NEXT_PUBLIC_APP_URL}/transactions" class="button">Track Your Order</a>
            </div>
          </div>
        </body>
      </html>
    `,
  }),

  saleNotification: (details: {
    sellerName: string;
    cardTitle: string;
    amount: number;
    buyerName: string;
  }) => ({
    subject: `🎉 You made a sale! ${details.cardTitle}`,
    html: `
      <!DOCTYPE html>
      <html>
        <body>
          <div class="container">
            <div class="header">
              <h1>🎉 Congratulations on your sale!</h1>
            </div>
            <div class="content">
              <h2>Hi ${details.sellerName},</h2>
              <p>Great news! Your card has been sold.</p>

              <div style="background: white; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h3>${details.cardTitle}</h3>
                <p><strong>Sale Price:</strong> $${details.amount.toLocaleString()}</p>
                <p><strong>Buyer:</strong> ${details.buyerName}</p>
                <p><strong>Your Earnings:</strong> $${(details.amount * 0.95).toLocaleString()} (after 5% fee)</p>
              </div>

              <p><strong>Next Steps:</strong></p>
              <ol>
                <li>Package the card securely</li>
                <li>Ship within 2 business days</li>
                <li>Upload tracking number</li>
                <li>Get paid automatically after delivery</li>
              </ol>

              <a href="${process.env.NEXT_PUBLIC_APP_URL}/dashboard" class="button">Ship Now</a>
            </div>
          </div>
        </body>
      </html>
    `,
  }),

  offerReceived: (details: {
    sellerName: string;
    cardTitle: string;
    offerAmount: number;
    buyerName: string;
  }) => ({
    subject: `💰 New Offer: ${details.cardTitle}`,
    html: `
      <!DOCTYPE html>
      <html>
        <body>
          <div class="container">
            <div class="header">
              <h1>💰 You received an offer!</h1>
            </div>
            <div class="content">
              <h2>Hi ${details.sellerName},</h2>
              <p>${details.buyerName} made an offer on your card:</p>

              <div style="background: white; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h3>${details.cardTitle}</h3>
                <p><strong>Offer Amount:</strong> $${details.offerAmount.toLocaleString()}</p>
              </div>

              <a href="${process.env.NEXT_PUBLIC_APP_URL}/offers" class="button">Review Offer</a>
            </div>
          </div>
        </body>
      </html>
    `,
  }),
};
