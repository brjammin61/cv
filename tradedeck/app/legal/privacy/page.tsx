'use client';

import Navbar from '@/components/Navbar';

export default function PrivacyPage() {
  return (
    <div className="min-h-screen">
      <Navbar />

      <div className="pt-24 pb-20 px-4">
        <div className="max-w-4xl mx-auto prose prose-blue">
          <h1>Privacy Policy</h1>
          <p className="text-gray-600">Last updated: {new Date().toLocaleDateString()}</p>

          <h2>1. Information We Collect</h2>

          <h3>Information You Provide</h3>
          <ul>
            <li><strong>Account Information:</strong> Email, name, password</li>
            <li><strong>Profile Information:</strong> Profile photo, bio, location (optional)</li>
            <li><strong>Listing Information:</strong> Card details, photos, descriptions</li>
            <li><strong>Payment Information:</strong> Processed by Stripe (we don't store card details)</li>
            <li><strong>Communications:</strong> Messages with other users, support tickets</li>
          </ul>

          <h3>Information Collected Automatically</h3>
          <ul>
            <li><strong>Usage Data:</strong> Pages visited, cards viewed, search queries</li>
            <li><strong>Device Information:</strong> Browser type, IP address, device type</li>
            <li><strong>Cookies:</strong> Authentication, preferences, analytics</li>
          </ul>

          <h2>2. How We Use Your Information</h2>
          <p>We use your information to:</p>
          <ul>
            <li>Provide and improve the Service</li>
            <li>Process transactions and payments</li>
            <li>Send transactional emails (purchase confirmations, shipping updates)</li>
            <li>Prevent fraud and enforce our Terms</li>
            <li>Personalize your experience</li>
            <li>Analyze usage patterns and improve features</li>
            <li>Send marketing emails (you can opt out)</li>
          </ul>

          <h2>3. Information Sharing</h2>
          <p>We share your information with:</p>

          <h3>Other Users</h3>
          <ul>
            <li>Your public profile (name, photo, rating) is visible to all users</li>
            <li>Buyers/sellers in transactions see shipping addresses</li>
            <li>Your listings are public</li>
          </ul>

          <h3>Service Providers</h3>
          <ul>
            <li><strong>Stripe:</strong> Payment processing</li>
            <li><strong>Cloudinary:</strong> Image hosting</li>
            <li><strong>SendGrid:</strong> Email delivery</li>
            <li><strong>Pusher:</strong> Real-time messaging</li>
            <li><strong>Vercel:</strong> Hosting</li>
          </ul>

          <h3>Legal Requirements</h3>
          <ul>
            <li>To comply with legal obligations</li>
            <li>To respond to law enforcement requests</li>
            <li>To protect our rights and prevent fraud</li>
          </ul>

          <h2>4. Data Retention</h2>
          <p>We retain your information:</p>
          <ul>
            <li>As long as your account is active</li>
            <li>As necessary to provide the Service</li>
            <li>To comply with legal obligations</li>
            <li>To resolve disputes</li>
          </ul>
          <p>You can request account deletion at any time.</p>

          <h2>5. Your Rights</h2>
          <p>You have the right to:</p>
          <ul>
            <li><strong>Access:</strong> Request a copy of your data</li>
            <li><strong>Correction:</strong> Update incorrect information</li>
            <li><strong>Deletion:</strong> Delete your account and data</li>
            <li><strong>Opt-out:</strong> Unsubscribe from marketing emails</li>
            <li><strong>Data Portability:</strong> Export your data</li>
          </ul>

          <h2>6. Security</h2>
          <p>We implement security measures to protect your information:</p>
          <ul>
            <li>HTTPS encryption for all data transmission</li>
            <li>Encrypted passwords (bcrypt)</li>
            <li>Regular security audits</li>
            <li>Limited employee access to personal data</li>
            <li>Secure cloud infrastructure</li>
          </ul>
          <p>
            However, no method of transmission over the Internet is 100% secure.
            We cannot guarantee absolute security.
          </p>

          <h2>7. Cookies and Tracking</h2>
          <p>We use cookies for:</p>
          <ul>
            <li><strong>Essential:</strong> Authentication, security, preferences</li>
            <li><strong>Analytics:</strong> Understanding how you use the Service</li>
            <li><strong>Marketing:</strong> Showing relevant ads (if applicable)</li>
          </ul>
          <p>You can disable cookies in your browser, but some features may not work.</p>

          <h2>8. Third-Party Links</h2>
          <p>
            Our Service may contain links to third-party websites. We are not responsible for
            the privacy practices of these sites. Please read their privacy policies.
          </p>

          <h2>9. Children's Privacy</h2>
          <p>
            Our Service is not intended for anyone under 18. We do not knowingly collect
            information from children. If you are a parent and believe your child has provided
            us with personal information, please contact us.
          </p>

          <h2>10. International Users</h2>
          <p>
            Your information may be transferred to and processed in countries other than your own.
            By using the Service, you consent to such transfers.
          </p>

          <h2>11. California Privacy Rights (CCPA)</h2>
          <p>California residents have additional rights:</p>
          <ul>
            <li>Right to know what personal information is collected</li>
            <li>Right to delete personal information</li>
            <li>Right to opt-out of sale of personal information (we don't sell data)</li>
            <li>Right to non-discrimination for exercising privacy rights</li>
          </ul>

          <h2>12. European Users (GDPR)</h2>
          <p>European users have rights under GDPR:</p>
          <ul>
            <li>Right to access your personal data</li>
            <li>Right to rectification of incorrect data</li>
            <li>Right to erasure ("right to be forgotten")</li>
            <li>Right to restrict processing</li>
            <li>Right to data portability</li>
            <li>Right to object to processing</li>
          </ul>
          <p>Our legal basis for processing is consent and contract performance.</p>

          <h2>13. Changes to Privacy Policy</h2>
          <p>
            We may update this Privacy Policy from time to time. We will notify you of
            significant changes via email or prominent notice on the Service.
          </p>

          <h2>14. Contact Us</h2>
          <p>
            For privacy-related questions or to exercise your rights, contact us at:<br />
            Email: privacy@tradedeck.com<br />
            Address: [Your Business Address]
          </p>

          <div className="bg-green-50 border border-green-200 rounded-lg p-6 my-8">
            <h3 className="mt-0">Privacy Summary</h3>
            <ul className="mb-0">
              <li>✅ We collect only what's needed to provide the Service</li>
              <li>✅ We never sell your personal information</li>
              <li>✅ You can delete your account anytime</li>
              <li>✅ We use industry-standard security</li>
              <li>✅ We're transparent about data usage</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
