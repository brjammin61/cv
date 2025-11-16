import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth/config';
import { prisma } from '@/lib/prisma';

// GET /api/cards/[id] - Get single card
export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const card = await prisma.card.findUnique({
      where: { id: params.id },
      include: {
        seller: {
          select: {
            id: true,
            name: true,
            image: true,
            rating: true,
            totalSales: true,
          },
        },
      },
    });

    if (!card) {
      return NextResponse.json({ error: 'Card not found' }, { status: 404 });
    }

    // Increment views
    await prisma.card.update({
      where: { id: params.id },
      data: { views: { increment: 1 } },
    });

    // Track page view
    await prisma.pageView.create({
      data: {
        path: `/cards/${params.id}`,
        cardId: params.id,
      },
    });

    return NextResponse.json(card);
  } catch (error) {
    console.error('Error fetching card:', error);
    return NextResponse.json({ error: 'Failed to fetch card' }, { status: 500 });
  }
}

// PUT /api/cards/[id] - Update card
export async function PUT(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await req.json();

    // Check ownership
    const card = await prisma.card.findUnique({
      where: { id: params.id },
    });

    if (!card || card.sellerId !== session.user.id) {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    const updatedCard = await prisma.card.update({
      where: { id: params.id },
      data: body,
    });

    return NextResponse.json(updatedCard);
  } catch (error) {
    console.error('Error updating card:', error);
    return NextResponse.json({ error: 'Failed to update card' }, { status: 500 });
  }
}

// DELETE /api/cards/[id] - Delete card
export async function DELETE(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const card = await prisma.card.findUnique({
      where: { id: params.id },
    });

    if (!card || card.sellerId !== session.user.id) {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    await prisma.card.delete({
      where: { id: params.id },
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error deleting card:', error);
    return NextResponse.json({ error: 'Failed to delete card' }, { status: 500 });
  }
}
