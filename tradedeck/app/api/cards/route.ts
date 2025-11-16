import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth/config';
import { prisma } from '@/lib/prisma';
import { z } from 'zod';

const createCardSchema = z.object({
  title: z.string().min(1),
  player: z.string().min(1),
  year: z.number().min(1800).max(new Date().getFullYear() + 1),
  sport: z.enum(['BASKETBALL', 'BASEBALL', 'FOOTBALL', 'SOCCER', 'HOCKEY', 'OTHER']),
  set: z.string().min(1),
  cardNumber: z.string().min(1),
  category: z.string().min(1),
  era: z.string().min(1),
  condition: z.enum(['MINT', 'NEAR_MINT', 'EXCELLENT', 'GOOD', 'FAIR', 'POOR']),
  graded: z.boolean(),
  grade: z.number().optional(),
  gradingCompany: z.enum(['PSA', 'BGS', 'SGC', 'CGC']).optional(),
  price: z.number().positive(),
  imageUrl: z.string().url(),
  images: z.array(z.string().url()).optional(),
  description: z.string().optional(),
  featured: z.boolean().optional(),
});

// GET /api/cards - List cards with filters
export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);

    const sport = searchParams.get('sport');
    const player = searchParams.get('player');
    const graded = searchParams.get('graded');
    const minPrice = searchParams.get('minPrice');
    const maxPrice = searchParams.get('maxPrice');
    const status = searchParams.get('status') || 'ACTIVE';
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '20');

    const where: any = {
      status,
    };

    if (sport) where.sport = sport;
    if (player) where.player = { contains: player, mode: 'insensitive' };
    if (graded) where.graded = graded === 'true';
    if (minPrice || maxPrice) {
      where.price = {};
      if (minPrice) where.price.gte = parseFloat(minPrice);
      if (maxPrice) where.price.lte = parseFloat(maxPrice);
    }

    const [cards, total] = await Promise.all([
      prisma.card.findMany({
        where,
        include: {
          seller: {
            select: {
              id: true,
              name: true,
              image: true,
              rating: true,
            },
          },
        },
        orderBy: { createdAt: 'desc' },
        skip: (page - 1) * limit,
        take: limit,
      }),
      prisma.card.count({ where }),
    ]);

    return NextResponse.json({
      cards,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    });
  } catch (error) {
    console.error('Error fetching cards:', error);
    return NextResponse.json({ error: 'Failed to fetch cards' }, { status: 500 });
  }
}

// POST /api/cards - Create a new card listing
export async function POST(req: NextRequest) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await req.json();
    const validatedData = createCardSchema.parse(body);

    const card = await prisma.card.create({
      data: {
        ...validatedData,
        sellerId: session.user.id,
      },
      include: {
        seller: {
          select: {
            id: true,
            name: true,
            image: true,
            rating: true,
          },
        },
      },
    });

    // Update user's total listings
    await prisma.user.update({
      where: { id: session.user.id },
      data: { totalListings: { increment: 1 } },
    });

    return NextResponse.json(card, { status: 201 });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({ error: error.errors }, { status: 400 });
    }
    console.error('Error creating card:', error);
    return NextResponse.json({ error: 'Failed to create card' }, { status: 500 });
  }
}
