'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  FiCheckCircle,
  FiCircle,
  FiServer,
  FiCreditCard,
  FiDatabase,
  FiGlobe,
  FiRocket,
  FiMessageSquare,
  FiShield,
  FiAlertCircle,
} from 'react-icons/fi';
import Navbar from '@/components/Navbar';

interface ChecklistItem {
  id: string;
  title: string;
  description: string;
  completed: boolean;
  critical: boolean;
}

interface ChecklistSection {
  title: string;
  icon: any;
  color: string;
  items: ChecklistItem[];
}

export default function LaunchChecklist() {
  const [checklist, setChecklist] = useState<ChecklistSection[]>([
    {
      title: '1. Environment Setup',
      icon: FiServer,
      color: 'from-blue-500 to-blue-600',
      items: [
        {
          id: 'env-1',
          title: 'Copy .env.example to .env',
          description: 'cp .env.example .env',
          completed: false,
          critical: true,
        },
        {
          id: 'env-2',
          title: 'Set DATABASE_URL',
          description: 'Get PostgreSQL connection string from Supabase/Railway',
          completed: false,
          critical: true,
        },
        {
          id: 'env-3',
          title: 'Generate NEXTAUTH_SECRET',
          description: 'openssl rand -base64 32',
          completed: false,
          critical: true,
        },
        {
          id: 'env-4',
          title: 'Set NEXTAUTH_URL',
          description: 'Your production domain (e.g., https://tradedeck.com)',
          completed: false,
          critical: true,
        },
      ],
    },
    {
      title: '2. Third-Party Services',
      icon: FiCreditCard,
      color: 'from-purple-500 to-purple-600',
      items: [
        {
          id: 'stripe-1',
          title: 'Create Stripe account',
          description: 'Sign up at stripe.com and get API keys',
          completed: false,
          critical: true,
        },
        {
          id: 'stripe-2',
          title: 'Enable Stripe Connect',
          description: 'Set up Connect for marketplace payments',
          completed: false,
          critical: true,
        },
        {
          id: 'stripe-3',
          title: 'Configure Stripe webhook',
          description: 'Add webhook endpoint: /api/webhooks/stripe',
          completed: false,
          critical: true,
        },
        {
          id: 'oauth-1',
          title: 'Set up Google OAuth',
          description: 'Create OAuth credentials in Google Cloud Console',
          completed: false,
          critical: false,
        },
        {
          id: 'oauth-2',
          title: 'Set up Facebook OAuth',
          description: 'Create app in Facebook Developers',
          completed: false,
          critical: false,
        },
        {
          id: 'oauth-3',
          title: 'Set up GitHub OAuth',
          description: 'Create OAuth app in GitHub settings',
          completed: false,
          critical: false,
        },
        {
          id: 'cloudinary-1',
          title: 'Create Cloudinary account',
          description: 'Sign up and get cloud name, API key, and secret',
          completed: false,
          critical: true,
        },
        {
          id: 'pusher-1',
          title: 'Create Pusher account',
          description: 'Sign up and create a new app for real-time features',
          completed: false,
          critical: true,
        },
        {
          id: 'email-1',
          title: 'Set up email service',
          description: 'Configure SendGrid, Mailgun, or SMTP credentials',
          completed: false,
          critical: true,
        },
      ],
    },
    {
      title: '3. Database Setup',
      icon: FiDatabase,
      color: 'from-green-500 to-green-600',
      items: [
        {
          id: 'db-1',
          title: 'Run database migrations',
          description: 'npx prisma migrate deploy',
          completed: false,
          critical: true,
        },
        {
          id: 'db-2',
          title: 'Generate Prisma client',
          description: 'npx prisma generate',
          completed: false,
          critical: true,
        },
        {
          id: 'db-3',
          title: 'Seed database',
          description: 'npm run seed (creates admin user and sample cards)',
          completed: false,
          critical: false,
        },
        {
          id: 'db-4',
          title: 'Verify database connection',
          description: 'npx prisma studio to inspect data',
          completed: false,
          critical: true,
        },
      ],
    },
    {
      title: '4. Domain & Deployment',
      icon: FiGlobe,
      color: 'from-orange-500 to-orange-600',
      items: [
        {
          id: 'domain-1',
          title: 'Purchase domain',
          description: 'Buy domain from Namecheap, GoDaddy, or Google Domains',
          completed: false,
          critical: true,
        },
        {
          id: 'deploy-1',
          title: 'Deploy to Vercel',
          description: 'Run: npm run deploy or vercel --prod',
          completed: false,
          critical: true,
        },
        {
          id: 'deploy-2',
          title: 'Add environment variables',
          description: 'Add all .env variables to Vercel dashboard',
          completed: false,
          critical: true,
        },
        {
          id: 'domain-2',
          title: 'Configure custom domain',
          description: 'Add domain to Vercel and update DNS records',
          completed: false,
          critical: true,
        },
        {
          id: 'deploy-3',
          title: 'Enable HTTPS',
          description: 'Vercel auto-provisions SSL certificates',
          completed: false,
          critical: true,
        },
      ],
    },
    {
      title: '5. Marketing Prep',
      icon: FiMessageSquare,
      color: 'from-pink-500 to-pink-600',
      items: [
        {
          id: 'marketing-1',
          title: 'Create social media accounts',
          description: 'Twitter, Instagram, Facebook, TikTok',
          completed: false,
          critical: false,
        },
        {
          id: 'marketing-2',
          title: 'Prepare launch posts',
          description: 'Use templates from /marketing/COPY_TEMPLATES.md',
          completed: false,
          critical: false,
        },
        {
          id: 'marketing-3',
          title: 'Build email list',
          description: 'Set up landing page or waitlist',
          completed: false,
          critical: false,
        },
        {
          id: 'marketing-4',
          title: 'Prepare Product Hunt launch',
          description: 'Schedule launch, prepare assets and first comment',
          completed: false,
          critical: false,
        },
        {
          id: 'marketing-5',
          title: 'Join card collector communities',
          description: 'Reddit, Facebook groups, Discord servers',
          completed: false,
          critical: false,
        },
      ],
    },
    {
      title: '6. Legal & Compliance',
      icon: FiShield,
      color: 'from-red-500 to-red-600',
      items: [
        {
          id: 'legal-1',
          title: 'Review Terms of Service',
          description: 'Customize /app/legal/terms with your business details',
          completed: false,
          critical: true,
        },
        {
          id: 'legal-2',
          title: 'Review Privacy Policy',
          description: 'Customize /app/legal/privacy with your business details',
          completed: false,
          critical: true,
        },
        {
          id: 'legal-3',
          title: 'Set up business entity',
          description: 'LLC, Corp, or Sole Proprietorship',
          completed: false,
          critical: false,
        },
        {
          id: 'legal-4',
          title: 'Get business insurance',
          description: 'General liability insurance (optional but recommended)',
          completed: false,
          critical: false,
        },
      ],
    },
    {
      title: '7. Pre-Launch Testing',
      icon: FiAlertCircle,
      color: 'from-yellow-500 to-yellow-600',
      items: [
        {
          id: 'test-1',
          title: 'Test authentication flow',
          description: 'Sign up, sign in, password reset',
          completed: false,
          critical: true,
        },
        {
          id: 'test-2',
          title: 'Test card listing',
          description: 'Create, edit, delete listings',
          completed: false,
          critical: true,
        },
        {
          id: 'test-3',
          title: 'Test purchase flow',
          description: 'Complete end-to-end transaction with test card',
          completed: false,
          critical: true,
        },
        {
          id: 'test-4',
          title: 'Test escrow system',
          description: 'Verify payment hold and release',
          completed: false,
          critical: true,
        },
        {
          id: 'test-5',
          title: 'Test real-time messaging',
          description: 'Send messages between users',
          completed: false,
          critical: true,
        },
        {
          id: 'test-6',
          title: 'Test email notifications',
          description: 'Verify all transactional emails send correctly',
          completed: false,
          critical: true,
        },
        {
          id: 'test-7',
          title: 'Mobile responsiveness',
          description: 'Test on iOS and Android devices',
          completed: false,
          critical: true,
        },
        {
          id: 'test-8',
          title: 'Cross-browser testing',
          description: 'Test on Chrome, Safari, Firefox, Edge',
          completed: false,
          critical: true,
        },
      ],
    },
    {
      title: '8. Go Live',
      icon: FiRocket,
      color: 'from-teal-500 to-teal-600',
      items: [
        {
          id: 'launch-1',
          title: 'Add initial card listings',
          description: 'Seed marketplace with 50-100 cards to avoid empty state',
          completed: false,
          critical: true,
        },
        {
          id: 'launch-2',
          title: 'Announce on social media',
          description: 'Post launch announcement on all channels',
          completed: false,
          critical: true,
        },
        {
          id: 'launch-3',
          title: 'Post on Reddit',
          description: 'r/sportscards, r/baseballcards, r/basketballcards',
          completed: false,
          critical: true,
        },
        {
          id: 'launch-4',
          title: 'Launch on Product Hunt',
          description: 'Post at 12:01am PST for maximum visibility',
          completed: false,
          critical: false,
        },
        {
          id: 'launch-5',
          title: 'Send launch email',
          description: 'Email your waitlist/subscribers',
          completed: false,
          critical: false,
        },
        {
          id: 'launch-6',
          title: 'Monitor analytics',
          description: 'Set up Google Analytics, track user behavior',
          completed: false,
          critical: false,
        },
        {
          id: 'launch-7',
          title: 'Respond to feedback',
          description: 'Engage with all comments and questions',
          completed: false,
          critical: true,
        },
      ],
    },
  ]);

  // Load completion state from localStorage
  useEffect(() => {
    const savedState = localStorage.getItem('tradedeck-launch-checklist');
    if (savedState) {
      setChecklist(JSON.parse(savedState));
    }
  }, []);

  // Save completion state to localStorage
  const toggleItem = (sectionIndex: number, itemId: string) => {
    const newChecklist = [...checklist];
    const item = newChecklist[sectionIndex].items.find((i) => i.id === itemId);
    if (item) {
      item.completed = !item.completed;
      setChecklist(newChecklist);
      localStorage.setItem('tradedeck-launch-checklist', JSON.stringify(newChecklist));
    }
  };

  const calculateProgress = () => {
    const totalItems = checklist.reduce((sum, section) => sum + section.items.length, 0);
    const completedItems = checklist.reduce(
      (sum, section) => sum + section.items.filter((i) => i.completed).length,
      0
    );
    return Math.round((completedItems / totalItems) * 100);
  };

  const calculateCriticalProgress = () => {
    const criticalItems = checklist
      .flatMap((section) => section.items)
      .filter((i) => i.critical);
    const completedCritical = criticalItems.filter((i) => i.completed);
    return Math.round((completedCritical.length / criticalItems.length) * 100);
  };

  const progress = calculateProgress();
  const criticalProgress = calculateCriticalProgress();

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <div className="pt-24 pb-20 px-4">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold mb-4">
              Launch <span className="bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">Checklist</span>
            </h1>
            <p className="text-xl text-gray-600">
              Follow these steps to launch TradeDeck successfully
            </p>
          </div>

          {/* Progress Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
            <div className="glass-effect rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold">Overall Progress</h3>
                <span className="text-2xl font-bold text-primary-600">{progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 1, ease: 'easeOut' }}
                  className="bg-gradient-to-r from-primary-600 to-accent-600 h-full rounded-full"
                />
              </div>
            </div>

            <div className="glass-effect rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold">Critical Tasks</h3>
                <span className="text-2xl font-bold text-red-600">{criticalProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${criticalProgress}%` }}
                  transition={{ duration: 1, ease: 'easeOut' }}
                  className="bg-gradient-to-r from-red-500 to-orange-500 h-full rounded-full"
                />
              </div>
            </div>
          </div>

          {/* Checklist Sections */}
          <div className="space-y-8">
            {checklist.map((section, sectionIndex) => {
              const sectionProgress = Math.round(
                (section.items.filter((i) => i.completed).length / section.items.length) * 100
              );

              return (
                <motion.div
                  key={section.title}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: sectionIndex * 0.1 }}
                  className="glass-effect rounded-2xl p-6"
                >
                  {/* Section Header */}
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-4">
                      <div
                        className={`w-12 h-12 rounded-xl bg-gradient-to-br ${section.color} flex items-center justify-center`}
                      >
                        <section.icon className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <h2 className="text-2xl font-bold">{section.title}</h2>
                        <p className="text-sm text-gray-600">
                          {section.items.filter((i) => i.completed).length} of{' '}
                          {section.items.length} completed
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-3xl font-bold text-primary-600">
                        {sectionProgress}%
                      </span>
                    </div>
                  </div>

                  {/* Section Items */}
                  <div className="space-y-3">
                    {section.items.map((item) => (
                      <button
                        key={item.id}
                        onClick={() => toggleItem(sectionIndex, item.id)}
                        className={`w-full flex items-start gap-4 p-4 rounded-xl transition-all ${
                          item.completed
                            ? 'bg-green-50 border-2 border-green-200'
                            : 'bg-white border-2 border-gray-200 hover:border-primary-300'
                        }`}
                      >
                        <div className="flex-shrink-0 mt-1">
                          {item.completed ? (
                            <FiCheckCircle className="w-6 h-6 text-green-600" />
                          ) : (
                            <FiCircle className="w-6 h-6 text-gray-400" />
                          )}
                        </div>
                        <div className="flex-1 text-left">
                          <div className="flex items-center gap-2 mb-1">
                            <h3
                              className={`font-semibold ${
                                item.completed ? 'text-green-900 line-through' : 'text-gray-900'
                              }`}
                            >
                              {item.title}
                            </h3>
                            {item.critical && !item.completed && (
                              <span className="px-2 py-0.5 text-xs font-bold text-red-600 bg-red-100 rounded-full">
                                CRITICAL
                              </span>
                            )}
                          </div>
                          <p
                            className={`text-sm ${
                              item.completed ? 'text-green-700' : 'text-gray-600'
                            }`}
                          >
                            {item.description}
                          </p>
                        </div>
                      </button>
                    ))}
                  </div>
                </motion.div>
              );
            })}
          </div>

          {/* Launch Ready Message */}
          {progress === 100 && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="mt-12 bg-gradient-to-r from-primary-600 to-accent-600 rounded-3xl p-8 text-center text-white"
            >
              <FiRocket className="w-16 h-16 mx-auto mb-4" />
              <h2 className="text-4xl font-bold mb-4">Ready to Launch!</h2>
              <p className="text-xl mb-6">
                All tasks completed. TradeDeck is ready to go live!
              </p>
              <button className="bg-white text-primary-600 px-8 py-3 rounded-full font-bold hover:bg-white/90 transition-colors">
                Launch TradeDeck
              </button>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
