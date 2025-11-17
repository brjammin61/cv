import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth/config';
import prisma from '@/lib/db/prisma';

export async function GET() {
  try {
    const session = await getServerSession(authOptions);

    if (!session || session.user.role !== 'ADMIN') {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 403 });
    }

    // Get current date for today's stats
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);

    // Parallel queries for better performance
    const [
      totalUsers,
      totalListings,
      totalRevenue,
      pendingDisputes,
      activeTransactions,
      newUsersToday,
      salesThisMonth,
      allTransactions,
    ] = await Promise.all([
      prisma.user.count(),
      prisma.card.count({ where: { status: 'ACTIVE' } }),
      prisma.transaction.aggregate({
        where: { status: 'COMPLETED' },
        _sum: { amount: true },
      }),
      prisma.dispute.count({ where: { status: 'OPEN' } }),
      prisma.transaction.count({
        where: {
          status: {
            in: ['PENDING', 'PAID', 'SHIPPED'],
          },
        },
      }),
      prisma.user.count({
        where: {
          createdAt: {
            gte: today,
          },
        },
      }),
      prisma.transaction.count({
        where: {
          status: 'COMPLETED',
          completedAt: {
            gte: startOfMonth,
          },
        },
      }),
      prisma.transaction.findMany({
        where: { status: 'COMPLETED' },
        select: { amount: true },
      }),
    ]);

    // Calculate average transaction value
    const averageTransactionValue =
      allTransactions.length > 0
        ? allTransactions.reduce((sum, t) => sum + t.amount, 0) / allTransactions.length
        : 0;

    const stats = {
      totalUsers,
      totalListings,
      totalRevenue: totalRevenue._sum.amount || 0,
      pendingDisputes,
      activeTransactions,
      newUsersToday,
      salesThisMonth,
      averageTransactionValue: Math.round(averageTransactionValue),
    };

    return NextResponse.json(stats);
  } catch (error) {
    console.error('Error fetching admin stats:', error);
    return NextResponse.json(
      { error: 'Failed to fetch stats' },
      { status: 500 }
    );
  }
}
