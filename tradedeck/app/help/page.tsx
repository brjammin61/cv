'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { FiChevronDown, FiChevronUp, FiSearch } from 'react-icons/fi';
import Navbar from '@/components/Navbar';

const faqs = [
  {
    category: 'Getting Started',
    questions: [
      {
        q: 'How do I create an account?',
        a: 'Click "Sign Up" in the top right. You can sign up with email, Google, Facebook, or GitHub. It takes less than 30 seconds!',
      },
      {
        q: 'Is TradeDeck free to use?',
        a: 'Yes! Creating an account and browsing is 100% free. We only charge a 5% fee when you successfully sell a card (much lower than eBay\'s 13%+).',
      },
      {
        q: 'What types of cards can I buy/sell?',
        a: 'All types of trading cards: sports cards (basketball, baseball, football, soccer, hockey), Pokémon, Magic: The Gathering, Yu-Gi-Oh, and more!',
      },
    ],
  },
  {
    category: 'Buying Cards',
    questions: [
      {
        q: 'How does the swipe feature work?',
        a: 'Set your filters (sport, player, price range, etc.) and cards will appear one at a time. Swipe right to like, left to pass, or up to make an offer. It\'s way more fun than traditional search!',
      },
      {
        q: 'Is my payment protected?',
        a: 'Absolutely! We use escrow to hold your payment securely until you receive the card and confirm it\'s as described. If there\'s an issue, we\'ll help resolve it or refund you.',
      },
      {
        q: 'How long does shipping take?',
        a: 'Most sellers ship within 1-2 business days. Typical delivery is 3-5 business days for domestic shipments. You\'ll get tracking information to monitor your package.',
      },
      {
        q: 'What if the card isn\'t as described?',
        a: 'You have 24 hours after delivery to report any issues. Open a dispute and we\'ll investigate. If the card truly isn\'t as described, you\'ll get a full refund.',
      },
      {
        q: 'Can I make an offer on a card?',
        a: 'Yes! Swipe up on any card or click "Make Offer" on the card detail page. The seller can accept, reject, or counter your offer.',
      },
    ],
  },
  {
    category: 'Selling Cards',
    questions: [
      {
        q: 'How do I list a card for sale?',
        a: 'Click "Sell" → "Add Card" → Upload photos, add details, set price → Publish! Takes about 60 seconds. Pro tip: Better photos = more sales.',
      },
      {
        q: 'What fees do you charge sellers?',
        a: 'Just 5% of the sale price. No listing fees, no monthly fees, no hidden charges. If you sell a $100 card, you keep $95.',
      },
      {
        q: 'When do I get paid?',
        a: 'Once the buyer receives the card and confirms delivery (tracked via shipping), there\'s a 24-hour hold period. After that, funds are automatically transferred to your account.',
      },
      {
        q: 'How should I ship cards?',
        a: 'Minimum: Card sleeve + toploader + bubble mailer. For expensive cards: Card saver + team bag + bubble mailer + cardboard reinforcement. Always use tracking!',
      },
      {
        q: 'What if a buyer opens a false dispute?',
        a: 'We investigate all disputes thoroughly. Provide your evidence (photos, messages, tracking). We protect honest sellers from fraudulent claims.',
      },
      {
        q: 'Can I offer bulk discounts?',
        a: 'Yes! Buyers can message you to discuss bulk purchases. You can also accept lower offers for multiple card purchases.',
      },
    ],
  },
  {
    category: 'Escrow & Safety',
    questions: [
      {
        q: 'How does escrow work?',
        a: 'When a buyer purchases your card: (1) Payment is held securely, (2) You ship the card, (3) Buyer receives and confirms, (4) After 24 hours, you get paid. Your money is protected the entire time.',
      },
      {
        q: 'What is the authentication service?',
        a: 'For high-value cards ($1000+), you can opt to have the card authenticated by PSA/BGS before it ships to the buyer. This adds $150 but provides maximum protection against counterfeits.',
      },
      {
        q: 'How do you prevent scams?',
        a: 'Multiple ways: (1) Escrow holds payment, (2) Verified seller ratings, (3) Required tracking on all shipments, (4) 24-hour dispute window, (5) We ban scammers permanently.',
      },
      {
        q: 'Are counterfeit cards allowed?',
        a: 'Absolutely not. Selling counterfeit items results in immediate account termination and potential legal action. We take this very seriously.',
      },
    ],
  },
  {
    category: 'Account & Settings',
    questions: [
      {
        q: 'How do I build my seller rating?',
        a: 'Ship quickly, package securely, describe accurately, communicate well. After each sale, buyers can leave a rating. 5-star sellers get featured placement!',
      },
      {
        q: 'Can I delete my account?',
        a: 'Yes, anytime. Go to Settings → Account → Delete Account. Note: You must complete all pending transactions first.',
      },
      {
        q: 'How do I change my email/password?',
        a: 'Go to Settings → Account → Update Email or Change Password. You\'ll receive a confirmation email.',
      },
      {
        q: 'Can I block other users?',
        a: 'Yes! Go to their profile → Click "..." → Block User. They won\'t be able to contact you or see your listings.',
      },
    ],
  },
  {
    category: 'Payments & Fees',
    questions: [
      {
        q: 'What payment methods do you accept?',
        a: 'All major credit/debit cards (Visa, Mastercard, Amex, Discover) via Stripe. We don\'t store your card information.',
      },
      {
        q: 'When is the 5% fee charged?',
        a: 'Only when a sale completes successfully. It\'s automatically deducted from your payout. No sale = no fee.',
      },
      {
        q: 'Do I need a business license to sell?',
        a: 'Not required for casual selling. If you\'re running a business, check your local laws. TradeDeck will send 1099-K forms if you sell $600+ per year.',
      },
      {
        q: 'How do refunds work?',
        a: 'Refunds are issued to the original payment method within 5-10 business days. The seller receives their card back (they pay return shipping).',
      },
    ],
  },
];

export default function HelpPage() {
  const [openQuestion, setOpenQuestion] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const filteredFaqs = faqs.map(category => ({
    ...category,
    questions: category.questions.filter(
      q =>
        q.q.toLowerCase().includes(searchQuery.toLowerCase()) ||
        q.a.toLowerCase().includes(searchQuery.toLowerCase())
    ),
  })).filter(category => category.questions.length > 0);

  return (
    <div className="min-h-screen">
      <Navbar />

      <div className="pt-24 pb-20 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold mb-4">
              How can we <span className="bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">help?</span>
            </h1>
            <p className="text-xl text-gray-600">Find answers to common questions</p>
          </div>

          {/* Search */}
          <div className="mb-12">
            <div className="relative max-w-2xl mx-auto">
              <FiSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search help articles..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-12 pr-4 py-4 rounded-xl glass-effect border border-white/20 focus:border-primary-500 focus:ring-4 focus:ring-primary-500/20 outline-none transition-all text-lg"
              />
            </div>
          </div>

          {/* FAQs */}
          {filteredFaqs.map((category) => (
            <div key={category.category} className="mb-8">
              <h2 className="text-2xl font-bold mb-4">{category.category}</h2>
              <div className="space-y-4">
                {category.questions.map((item, index) => {
                  const questionId = `${category.category}-${index}`;
                  const isOpen = openQuestion === questionId;

                  return (
                    <motion.div
                      key={questionId}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="glass-effect rounded-xl overflow-hidden"
                    >
                      <button
                        onClick={() => setOpenQuestion(isOpen ? null : questionId)}
                        className="w-full flex items-center justify-between p-6 text-left hover:bg-primary-50/50 transition-colors"
                      >
                        <span className="font-semibold text-lg pr-4">{item.q}</span>
                        {isOpen ? (
                          <FiChevronUp className="w-6 h-6 text-primary-600 flex-shrink-0" />
                        ) : (
                          <FiChevronDown className="w-6 h-6 text-gray-400 flex-shrink-0" />
                        )}
                      </button>
                      {isOpen && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="px-6 pb-6"
                        >
                          <p className="text-gray-700 leading-relaxed">{item.a}</p>
                        </motion.div>
                      )}
                    </motion.div>
                  );
                })}
              </div>
            </div>
          ))}

          {filteredFaqs.length === 0 && (
            <div className="text-center py-12">
              <p className="text-xl text-gray-600">No results found for "{searchQuery}"</p>
              <p className="text-gray-500 mt-2">Try a different search term</p>
            </div>
          )}

          {/* Contact Support */}
          <div className="mt-16 bg-gradient-to-r from-primary-600 to-accent-600 rounded-3xl p-8 text-center text-white">
            <h2 className="text-3xl font-bold mb-4">Still have questions?</h2>
            <p className="text-xl mb-6 text-white/90">We're here to help!</p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a
                href="mailto:support@tradedeck.com"
                className="bg-white text-primary-600 px-8 py-3 rounded-full font-bold hover:bg-white/90 transition-colors"
              >
                Email Support
              </a>
              <button className="bg-white/10 backdrop-blur-sm text-white px-8 py-3 rounded-full font-bold border-2 border-white hover:bg-white/20 transition-colors">
                Live Chat
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
