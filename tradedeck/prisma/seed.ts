import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcrypt';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Seeding database...');

  // Create admin user
  const adminPassword = await bcrypt.hash('admin123', 10);
  const admin = await prisma.user.upsert({
    where: { email: 'admin@tradedeck.com' },
    update: {},
    create: {
      email: 'admin@tradedeck.com',
      name: 'TradeDeck Admin',
      password: adminPassword,
      role: 'ADMIN',
      emailVerified: new Date(),
    },
  });

  console.log('✓ Created admin user:', admin.email);

  // Create demo seller
  const sellerPassword = await bcrypt.hash('seller123', 10);
  const seller = await prisma.user.upsert({
    where: { email: 'seller@tradedeck.com' },
    update: {},
    create: {
      email: 'seller@tradedeck.com',
      name: 'Demo Seller',
      password: sellerPassword,
      role: 'SELLER',
      rating: 4.8,
      totalSales: 45,
      emailVerified: new Date(),
    },
  });

  console.log('✓ Created demo seller:', seller.email);

  // Create sample cards
  const sampleCards = [
    {
      title: '2003-04 Topps Chrome Refractor',
      player: 'LeBron James',
      year: 2003,
      sport: 'BASKETBALL',
      set: 'Topps Chrome',
      cardNumber: '111',
      category: 'Basketball',
      era: '2000s',
      condition: 'MINT',
      graded: true,
      grade: 9.5,
      gradingCompany: 'BGS',
      price: 45000,
      imageUrl: 'https://via.placeholder.com/400x600/0ea5e9/ffffff?text=LeBron+Rookie',
      description: 'LeBron James rookie refractor. BGS 9.5 gem mint. One of the most iconic basketball cards ever produced.',
      sellerId: seller.id,
      featured: true,
    },
    {
      title: '1997-98 Metal Universe Precious Metal Gems',
      player: 'Michael Jordan',
      year: 1997,
      sport: 'BASKETBALL',
      set: 'Metal Universe PMG',
      cardNumber: '23',
      category: 'Basketball',
      era: '1990s',
      condition: 'NEAR_MINT',
      graded: true,
      grade: 9,
      gradingCompany: 'PSA',
      price: 125000,
      imageUrl: 'https://via.placeholder.com/400x600/d946ef/ffffff?text=MJ+PMG',
      description: 'Extremely rare PSA 9 Michael Jordan PMG. One of the holy grails of basketball cards.',
      sellerId: seller.id,
      featured: true,
    },
    {
      title: '2018 Panini Prizm Silver',
      player: 'Luka Doncic',
      year: 2018,
      sport: 'BASKETBALL',
      set: 'Prizm',
      cardNumber: '280',
      category: 'Basketball',
      era: '2010s',
      condition: 'MINT',
      graded: true,
      grade: 10,
      gradingCompany: 'PSA',
      price: 8500,
      imageUrl: 'https://via.placeholder.com/400x600/0ea5e9/ffffff?text=Luka+Rookie',
      description: 'Luka Doncic rookie silver prizm. PSA 10. One of the hottest rookies in the hobby.',
      sellerId: seller.id,
      featured: true,
    },
    {
      title: '1952 Topps Baseball',
      player: 'Mickey Mantle',
      year: 1952,
      sport: 'BASEBALL',
      set: 'Topps',
      cardNumber: '311',
      category: 'Baseball',
      era: 'Vintage',
      condition: 'EXCELLENT',
      graded: true,
      grade: 8,
      gradingCompany: 'PSA',
      price: 850000,
      imageUrl: 'https://via.placeholder.com/400x600/d946ef/ffffff?text=Mantle+52',
      description: 'The holy grail of baseball cards. PSA 8. Museum quality piece.',
      sellerId: seller.id,
      featured: true,
    },
    {
      title: '2017-18 National Treasures Autograph',
      player: 'Giannis Antetokounmpo',
      year: 2017,
      sport: 'BASKETBALL',
      set: 'National Treasures',
      cardNumber: '125',
      category: 'Basketball',
      era: '2010s',
      condition: 'MINT',
      graded: true,
      grade: 10,
      gradingCompany: 'PSA',
      price: 12000,
      imageUrl: 'https://via.placeholder.com/400x600/0ea5e9/ffffff?text=Giannis+Auto',
      description: 'Giannis Antetokounmpo autographed patch card. Numbered to 99. PSA 10.',
      sellerId: seller.id,
    },
    {
      title: '2000 Playoff Contenders Championship Ticket',
      player: 'Tom Brady',
      year: 2000,
      sport: 'FOOTBALL',
      set: 'Playoff Contenders',
      cardNumber: '144',
      category: 'Football',
      era: '2000s',
      condition: 'MINT',
      graded: true,
      grade: 9,
      gradingCompany: 'PSA',
      price: 175000,
      imageUrl: 'https://via.placeholder.com/400x600/d946ef/ffffff?text=Brady+Rookie+Auto',
      description: 'Tom Brady autographed rookie. PSA 9. The most valuable football card in the hobby.',
      sellerId: seller.id,
      featured: true,
    },
  ];

  for (const cardData of sampleCards) {
    const card = await prisma.card.create({
      data: cardData,
    });
    console.log(`✓ Created card: ${card.player} - ${card.title}`);
  }

  console.log('');
  console.log('🎉 Seeding complete!');
  console.log('');
  console.log('Demo accounts:');
  console.log('  Admin: admin@tradedeck.com / admin123');
  console.log('  Seller: seller@tradedeck.com / seller123');
  console.log('');
  console.log(`Created ${sampleCards.length} sample cards`);
}

main()
  .catch((e) => {
    console.error('Error seeding database:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
