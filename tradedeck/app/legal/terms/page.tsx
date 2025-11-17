'use client';

import Navbar from '@/components/Navbar';

export default function TermsPage() {
  return (
    <div className="min-h-screen">
      <Navbar />

      <div className="pt-24 pb-20 px-4">
        <div className="max-w-4xl mx-auto prose prose-blue">
          <h1>Terms of Service</h1>
          <p className="text-gray-600">Last updated: {new Date().toLocaleDateString()}</p>

          <h2>1. Agreement to Terms</h2>
          <p>
            By accessing or using TradeDeck ("Service"), you agree to be bound by these Terms of Service.
            If you disagree with any part of these terms, you may not access the Service.
          </p>

          <h2>2. Description of Service</h2>
          <p>
            TradeDeck is an online marketplace that connects buyers and sellers of trading cards.
            We provide the platform, payment processing, and escrow services to facilitate transactions.
          </p>

          <h2>3. User Accounts</h2>
          <h3>Registration</h3>
          <ul>
            <li>You must be at least 18 years old to use the Service</li>
            <li>You must provide accurate, current, and complete information</li>
            <li>You are responsible for maintaining the security of your account</li>
            <li>You are responsible for all activities under your account</li>
          </ul>

          <h2>4. Marketplace Rules</h2>

          <h3>For Sellers</h3>
          <ul>
            <li>You must own the items you list</li>
            <li>Item descriptions must be accurate and truthful</li>
            <li>You must ship items within 2 business days of sale</li>
            <li>You must provide tracking information</li>
            <li>You accept our 5% transaction fee on all sales</li>
            <li>Items must be as described or you risk disputes/refunds</li>
          </ul>

          <h3>For Buyers</h3>
          <ul>
            <li>You commit to purchasing when you complete checkout</li>
            <li>You have 24 hours after delivery to report issues</li>
            <li>Disputes must be legitimate and evidence-based</li>
            <li>Chargebacks may result in account suspension</li>
          </ul>

          <h2>5. Fees and Payments</h2>
          <h3>Transaction Fees</h3>
          <ul>
            <li>We charge sellers a 5% transaction fee on each sale</li>
            <li>Buyers pay the listed price plus shipping</li>
            <li>Optional authentication services incur additional fees</li>
          </ul>

          <h3>Escrow Process</h3>
          <ul>
            <li>Payments are held in escrow until delivery is confirmed</li>
            <li>Funds are released 24 hours after delivery (tracked shipments)</li>
            <li>Disputes pause fund release until resolved</li>
          </ul>

          <h2>6. Prohibited Items</h2>
          <p>You may not list:</p>
          <ul>
            <li>Counterfeit or fake cards</li>
            <li>Stolen property</li>
            <li>Items that violate intellectual property rights</li>
            <li>Illegal items or items promoting illegal activity</li>
            <li>Items misrepresented as authenticated when they are not</li>
          </ul>

          <h2>7. Intellectual Property</h2>
          <p>
            The Service and its original content, features, and functionality are owned by TradeDeck
            and are protected by international copyright, trademark, and other intellectual property laws.
          </p>

          <h2>8. Disputes and Refunds</h2>
          <ul>
            <li>Buyers must report issues within 24 hours of delivery</li>
            <li>Valid disputes: Item not as described, damaged, or never arrived</li>
            <li>We investigate all disputes and make final determinations</li>
            <li>Refunds are issued to the original payment method</li>
            <li>Abusing the dispute system may result in account termination</li>
          </ul>

          <h2>9. Privacy and Data</h2>
          <p>
            Your use of the Service is also governed by our Privacy Policy.
            By using the Service, you consent to our collection and use of personal data.
          </p>

          <h2>10. Termination</h2>
          <p>
            We may terminate or suspend your account immediately, without prior notice, for:
          </p>
          <ul>
            <li>Breach of these Terms</li>
            <li>Fraudulent activity</li>
            <li>Selling counterfeit items</li>
            <li>Repeated disputes or chargebacks</li>
            <li>Any conduct we deem harmful to the marketplace</li>
          </ul>

          <h2>11. Limitation of Liability</h2>
          <p>
            TradeDeck provides a platform for buyers and sellers to connect. We are not responsible for:
          </p>
          <ul>
            <li>The quality, safety, or legality of items listed</li>
            <li>The truth or accuracy of listings</li>
            <li>The ability of sellers to sell or buyers to pay</li>
            <li>Lost, stolen, or damaged shipments (beyond escrow protection)</li>
          </ul>

          <p>
            IN NO EVENT SHALL TRADEDECK BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL,
            CONSEQUENTIAL OR PUNITIVE DAMAGES ARISING OUT OF YOUR USE OF THE SERVICE.
          </p>

          <h2>12. Indemnification</h2>
          <p>
            You agree to indemnify and hold TradeDeck harmless from any claims, damages, or expenses
            arising from your use of the Service or violation of these Terms.
          </p>

          <h2>13. Changes to Terms</h2>
          <p>
            We reserve the right to modify these terms at any time. We will notify users of significant
            changes via email. Continued use of the Service constitutes acceptance of modified terms.
          </p>

          <h2>14. Governing Law</h2>
          <p>
            These Terms shall be governed by the laws of [Your State/Country], without regard to
            conflict of law provisions.
          </p>

          <h2>15. Contact Information</h2>
          <p>
            For questions about these Terms, contact us at:<br />
            Email: legal@tradedeck.com<br />
            Address: [Your Business Address]
          </p>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 my-8">
            <h3 className="mt-0">Summary (Not Legal Advice)</h3>
            <ul className="mb-0">
              <li>Be honest in your listings</li>
              <li>Ship promptly with tracking</li>
              <li>We take 5% on sales</li>
              <li>Escrow protects everyone</li>
              <li>No counterfeit items, ever</li>
              <li>Disputes get resolved fairly</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
