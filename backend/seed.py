from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from extensions import db
from models import (
    User, Product, Order, OrderItem, Wallet, Announcement, Review, SellerReview,
)


def seed_db():
    if User.query.first():
        return

    now = datetime.utcnow()
    pw  = generate_password_hash('123456')

    # ── Core accounts ────────────────────────────────────────
    admin  = User(username='admin',   email='admin@shophub.com',
                  password=generate_password_hash('admin123'),
                  role='admin',  enabled=True, created_at=now)
    seller = User(username='seller1', email='seller1@example.com',
                  password=pw, role='seller', shop_name='TechStore Pro',
                  enabled=True, created_at=now)
    buyer  = User(username='buyer1',  email='buyer1@example.com',
                  password=pw, role='buyer',  enabled=True, created_at=now)
    db.session.add_all([admin, seller, buyer])
    db.session.flush()

    # ── Fake reviewer accounts ────────────────────────────────
    reviewers_data = [
        ('alice_m',   'alice.m@mail.com'),
        ('bob_k',     'bob.k@mail.com'),
        ('charlie_l', 'charlie.l@mail.com'),
        ('diana_w',   'diana.w@mail.com'),
        ('eric_t',    'eric.t@mail.com'),
        ('fiona_h',   'fiona.h@mail.com'),
        ('george_p',  'george.p@mail.com'),
        ('helen_c',   'helen.c@mail.com'),
        ('ivan_r',    'ivan.r@mail.com'),
        ('julia_n',   'julia.n@mail.com'),
    ]
    reviewers = []
    for i, (uname, email) in enumerate(reviewers_data):
        u = User(username=uname, email=email, password=pw, role='buyer',
                 enabled=True, created_at=now - timedelta(days=60 + i * 5))
        db.session.add(u)
        reviewers.append(u)
    db.session.flush()

    # ── Products (Seller 1 — TechStore Pro) ──────────────────
    products = [
        Product(seller_id=seller.id, name='Wireless Bluetooth Earbuds', category='Electronics',
                price=99,  original_price=199, stock=49, emoji='🎧',
                description='Experience hi-fi stereo sound with 40mm drivers and active noise cancellation. Up to 24 hours battery life with the charging case. IPX5 water-resistant. Multipoint connection — pair with two devices simultaneously. Soft memory-foam ear tips included in three sizes.'),
        Product(seller_id=seller.id, name='Smart Watch Series 5', category='Electronics',
                price=199, original_price=399, stock=28, emoji='⌚',
                description='Always-on AMOLED display with 500 nit brightness. Built-in GPS, optical heart-rate sensor, SpO₂ monitor and sleep tracking. 7-day battery life. 5ATM water resistance. Compatible with both iOS and Android via the ShopHub Health app.'),
        Product(seller_id=seller.id, name='USB-C Fast Charger 65W', category='Electronics',
                price=49,  stock=100, emoji='🔌',
                description='GaN III technology delivers 65W in a palm-sized adapter — 60% smaller than conventional chargers. Dual USB-C ports plus one USB-A. Smart power distribution automatically adjusts wattage. Compatible with laptops, phones, tablets and gaming handhelds. Foldable US/EU plug.'),
        Product(seller_id=seller.id, name='Mechanical Keyboard TKL', category='Electronics',
                price=259, original_price=349, stock=19, emoji='⌨️',
                description='Tenkeyless layout for more desk space without sacrificing function keys. PBT double-shot keycaps with per-key RGB backlighting. CNC-machined aluminium top case with gasket mounting for a refined, bouncy typing feel. Hot-swap sockets — change switches in seconds. USB-C detachable cable included.'),
        Product(seller_id=seller.id, name='Korean Oversized Hoodie', category='Fashion',
                price=89,  stock=80, emoji='🧥',
                description='Heavyweight 380gsm 100% combed cotton fleece for ultimate softness. Dropped-shoulder relaxed fit inspired by Seoul streetwear. Ribbed cuffs and hem, kangaroo pocket, adjustable drawstring hood. Pre-washed to prevent shrinkage. Available in 8 colorways: Oat, Sage, Sand, Charcoal, Navy, Dusty Rose, Cream and Black.'),
        Product(seller_id=seller.id, name='Running Sneakers Air Pro', category='Sports',
                price=159, original_price=320, stock=58, emoji='👟',
                description='Engineered mesh upper with targeted ventilation zones keeps feet cool on long runs. Dual-density foam midsole with air cushion heel unit absorbs impact. Rubber outsole with multi-directional traction pattern. Reflective detailing for low-light visibility. Available in full and half sizes 36–46.'),
        Product(seller_id=seller.id, name='Insulated Water Bottle', category='Sports',
                price=39,  original_price=89,  stock=198, emoji='🥤',
                description='Double-wall vacuum insulation keeps drinks cold 24 hours and hot 12 hours. 18/8 food-grade stainless steel, BPA-free. Leak-proof lid with carry loop. Wide mouth fits ice cubes and is dishwasher safe. 750ml capacity. Powder-coated exterior for grip.'),
        Product(seller_id=seller.id, name='Viral Snack Gift Box', category='Food',
                price=59,  stock=150, emoji='🍿',
                description='Curated selection of 20 premium snacks sourced from Japan, South Korea, Taiwan and Thailand. Includes limited-edition flavours not sold in western markets. Each box is individually sealed for freshness and comes with a flavour guide card. Perfect for gifting or weekly snack subscription.'),
        # Two extra products for seller1 — bringing TechStore Pro up to 10
        Product(seller_id=seller.id, name='Portable SSD 1TB USB-C', category='Electronics',
                price=129, original_price=189, stock=64, emoji='💾',
                description='Pocket-sized 1TB external SSD with USB 3.2 Gen 2 interface — sustained read/write up to 1050 MB/s. Aluminium shell with rubberised bumper. Shock-resistant to 2m drops. Cross-platform: works with Windows, macOS, Android, PS5 and Xbox out of the box. AES-256 hardware encryption.'),
        Product(seller_id=seller.id, name='4K Webcam with Ring Light', category='Electronics',
                price=149, stock=42, emoji='📷',
                description='Sony 1/2.8" sensor delivers true 4K30 video for streaming and calls. Built-in adjustable LED ring with three colour temperatures. Dual omnidirectional mics with AI noise suppression. Privacy shutter and tripod mount. Plug-and-play USB-C — no drivers needed.'),
    ]
    db.session.add_all(products)
    db.session.flush()

    # ── Wallets ───────────────────────────────────────────────
    db.session.add(Wallet(user_id=seller.id, balance=0))
    db.session.add(Wallet(user_id=buyer.id,  balance=1000))
    for r in reviewers:
        db.session.add(Wallet(user_id=r.id, balance=500))
    db.session.flush()

    # ── Orders for buyer1 (demo) ──────────────────────────────
    o1 = Order(buyer_id=buyer.id, status='completed', total=99,  created_at=now - timedelta(days=3))
    o2 = Order(buyer_id=buyer.id, status='completed', total=318, created_at=now - timedelta(days=1))
    db.session.add_all([o1, o2])
    db.session.flush()
    db.session.add(OrderItem(order_id=o1.id, product_id=products[0].id,
                             seller_id=seller.id, name=products[0].name, price=99,  qty=1))
    db.session.add(OrderItem(order_id=o2.id, product_id=products[5].id,
                             seller_id=seller.id, name=products[5].name, price=159, qty=2))

    # ── Orders for fake reviewers (so reviews pass the bought-check) ──
    def make_order(buyer_user, product, qty, days_ago):
        o = Order(buyer_id=buyer_user.id, status='completed',
                  total=product.price * qty,
                  created_at=now - timedelta(days=days_ago))
        db.session.add(o)
        db.session.flush()
        db.session.add(OrderItem(order_id=o.id, product_id=product.id,
                                 seller_id=product.seller_id, name=product.name,
                                 price=product.price, qty=qty))

    a, b, c, d, e, f, g, h, iv, j = reviewers

    make_order(a, products[0], 1, 30); make_order(b, products[0], 1, 25)
    make_order(c, products[0], 1, 20); make_order(d, products[0], 1, 18)
    make_order(e, products[0], 1, 15)

    make_order(f, products[1], 1, 28); make_order(g, products[1], 1, 22)
    make_order(h, products[1], 1, 19); make_order(iv, products[1], 1, 14)

    make_order(j, products[2], 1, 27); make_order(a, products[2], 1, 21)
    make_order(b, products[2], 1, 16)

    make_order(c, products[3], 1, 35); make_order(d, products[3], 1, 29)
    make_order(e, products[3], 1, 23); make_order(f, products[3], 1, 17)

    make_order(g, products[4], 1, 33); make_order(h, products[4], 1, 26)
    make_order(iv, products[4], 1, 20)

    make_order(j, products[5], 1, 31); make_order(a, products[5], 1, 24)
    make_order(b, products[5], 1, 18); make_order(c, products[5], 1, 12)

    make_order(d, products[6], 1, 28); make_order(e, products[6], 1, 22)
    make_order(f, products[6], 1, 15)

    make_order(g, products[7], 1, 29); make_order(h, products[7], 1, 23)
    make_order(iv, products[7], 1, 17); make_order(j, products[7], 1, 11)

    # Orders for the two NEW seller1 products
    make_order(a, products[8], 1, 14); make_order(b, products[8], 1, 9)
    make_order(c, products[9], 1, 12); make_order(d, products[9], 1, 7)

    # ── Reviews ───────────────────────────────────────────────
    def rev(user, product, rating, comment, days_ago):
        db.session.add(Review(
            product_id=product.id, user_id=user.id, username=user.username,
            rating=rating, comment=comment,
            created_at=now - timedelta(days=days_ago),
        ))

    # Product 0 — Wireless Bluetooth Earbuds
    rev(a, products[0], 5, "Absolutely love these! Crystal clear sound and the noise cancellation is top-notch. Best earbuds I've owned — worth every yuan.", 28)
    rev(b, products[0], 4, "Great sound quality for the price. Battery life is impressive — easily 20+ hours with the case. Would buy again without hesitation.", 23)
    rev(c, products[0], 5, "Exceeded my expectations. Comfortable fit even after hours, great bass, and the case charges them super quickly.", 18)
    rev(d, products[0], 3, "Sound is decent but the fit could be better for smaller ears. Call quality is clear though. Packaging was nice.", 16)
    rev(e, products[0], 5, "These are incredible. ANC works really well on the subway. My colleagues can't hear my music at max volume. Highly recommended!", 13)

    # Product 1 — Smart Watch Series 5
    rev(f, products[1], 5, "Gorgeous AMOLED display and tracks everything accurately. Sleep tracking has genuinely improved my daily routine.", 25)
    rev(g, products[1], 4, "Really solid watch. GPS locks on in seconds and the heart rate monitor matches my chest strap closely.", 20)
    rev(h, products[1], 5, "Already retired my old fitness tracker. 7-day battery is no joke — I charged it once this week.", 17)
    rev(iv, products[1], 3, "Feature-rich but the companion app takes some getting used to. Good value overall, just a learning curve.", 12)

    # Product 2 — USB-C Fast Charger 65W
    rev(j, products[2], 5, "Charges my laptop in under an hour and my phone in 30 minutes. Small, light, and runs cool. Perfect travel companion.", 24)
    rev(a, products[2], 5, "Works perfectly with my MacBook Pro and phone simultaneously. GaN tech really makes a size difference over my old brick.", 19)
    rev(b, products[2], 4, "Fast and reliable. No overheating, no throttling. Does exactly what it says on the box — that's all I need.", 14)

    # Product 3 — Mechanical Keyboard TKL
    rev(c, products[3], 5, "Best keyboard I've ever typed on. The tactile feedback is deeply satisfying without being annoyingly loud for office use.", 32)
    rev(d, products[3], 4, "Amazing build quality — the aluminium frame feels genuinely premium. RGB lighting has tons of effects to choose from.", 26)
    rev(e, products[3], 5, "Switched from a membrane keyboard and cannot go back. This thing is an absolute tank. Hot-swap sockets are a great bonus.", 21)
    rev(f, products[3], 4, "Solid keyboard. Switches are smooth and consistent. TKL layout is perfect for keeping the mouse close. Worth the price.", 15)

    # Product 4 — Korean Oversized Hoodie
    rev(g, products[4], 5, "So soft and cosy! The oversized fit is exactly right — not sloppy, just relaxed. Already ordered two more colours.", 30)
    rev(h, products[4], 4, "Great quality cotton, noticeably heavier than your average hoodie. Fits true to the description. A new wardrobe staple.", 24)
    rev(iv, products[4], 5, "Washed it five times and it still looks and feels brand new. The pre-wash really works. Love the colour options.", 18)

    # Product 5 — Running Sneakers Air Pro
    rev(j, products[5], 5, "Super lightweight and breathable. Wore them for a 10K straight out of the box — zero blisters. My feet are grateful.", 28)
    rev(a, products[5], 4, "Comfortable right out of the box with no break-in period needed. Good grip on asphalt. Only wish there were more colours.", 22)
    rev(b, products[5], 5, "These are my new go-to training shoes. Cushioning handles daily 10K runs without any knee discomfort. Highly recommended.", 16)
    rev(c, products[5], 4, "Fit true to size and very comfortable for both running and casual errands. The reflective detail is a nice safety touch.", 10)

    # Product 6 — Insulated Water Bottle
    rev(d, products[6], 5, "Kept my coffee hot for 14 hours on a cold day. Zero leaks in my bag. The powder coat gives a great non-slip grip.", 25)
    rev(e, products[6], 5, "Best water bottle I've ever used. Cold drinks stayed cold all afternoon in 35°C heat. The wide mouth fits ice cubes easily.", 19)
    rev(f, products[6], 4, "Solid stainless steel that feels durable. Cap opens and closes smoothly. Dishwasher-safe lid is a big plus for me.", 13)

    # Product 7 — Viral Snack Gift Box
    rev(g, products[7], 5, "What a fun box! Tried so many snacks I'd never come across before. The matcha wafers from Japan were my favourite. Perfect gift.", 26)
    rev(h, products[7], 4, "Really fun variety pack. Some were incredible, a couple weren't my taste — but that's the whole point of trying new things!", 20)
    rev(iv, products[7], 5, "Sent this as a birthday gift. My friend video-called me opening every single snack. She loved them all. Will order again.", 14)
    rev(j, products[7], 5, "Incredible assortment from across Asia. The flavour guide card is a thoughtful touch. Beautiful packaging too.", 9)

    # Product 8 — Portable SSD 1TB
    rev(a, products[8], 5, "Tiny, fast, and rock-solid. Backed up 800GB of footage in under 15 minutes. Highly recommended for creators.", 13)
    rev(b, products[8], 4, "Sustained speeds are real — no slowdowns even on huge file transfers. Build quality feels premium.", 8)

    # Product 9 — 4K Webcam
    rev(c, products[9], 5, "Massive upgrade from my laptop camera. The ring light is a nice touch for evening calls. Mic is surprisingly clear.", 11)
    rev(d, products[9], 4, "Crisp 4K image and the privacy shutter gives me peace of mind. Plug-and-play just worked on Windows and macOS.", 6)

    # ════════════════════════════════════════════════════════════
    # ── NEW SELLERS (4 more, 10 products each) ──────────────────
    # ════════════════════════════════════════════════════════════

    seller2 = User(username='seller2', email='seller2@example.com',
                   password=pw, role='seller', shop_name='Seoul Style Co.',
                   enabled=True, created_at=now - timedelta(days=200))
    seller3 = User(username='seller3', email='seller3@example.com',
                   password=pw, role='seller', shop_name='HomeNest',
                   enabled=True, created_at=now - timedelta(days=180))
    seller4 = User(username='seller4', email='seller4@example.com',
                   password=pw, role='seller', shop_name='GlowUp Beauty',
                   enabled=True, created_at=now - timedelta(days=160))
    seller5 = User(username='seller5', email='seller5@example.com',
                   password=pw, role='seller', shop_name='PeakFit Sports',
                   enabled=True, created_at=now - timedelta(days=140))
    db.session.add_all([seller2, seller3, seller4, seller5])
    db.session.flush()
    db.session.add_all([
        Wallet(user_id=seller2.id, balance=0),
        Wallet(user_id=seller3.id, balance=0),
        Wallet(user_id=seller4.id, balance=0),
        Wallet(user_id=seller5.id, balance=0),
    ])

    # ── Seller 2 — Seoul Style Co. (Fashion) ──────────────────
    p_seoul = [
        Product(seller_id=seller2.id, name='Cropped Denim Jacket', category='Fashion',
                price=119, original_price=189, stock=72, emoji='🧥',
                description='Vintage-wash mid-blue denim cropped at the waist for layering over dresses or high-rise jeans. 100% cotton, slightly distressed at cuffs and hem. Two chest pockets with antique brass buttons. Sizes XS–XXL.'),
        Product(seller_id=seller2.id, name='Pleated Mini Skirt', category='Fashion',
                price=69,  stock=88, emoji='👗',
                description='Lightweight crepe with sharp accordion pleats and an elastic waistband for everyday comfort. Hits just above the knee. Pairs beautifully with chunky knits or oversized tees. Six colours available.'),
        Product(seller_id=seller2.id, name='Wide-Leg Linen Pants', category='Fashion',
                price=99,  original_price=149, stock=60, emoji='👖',
                description='Breathable 100% French linen with a relaxed wide-leg silhouette. Side pockets, hidden zip and side-tab waist adjusters. Perfect for hot summers. Pre-shrunk and OEKO-TEX certified.'),
        Product(seller_id=seller2.id, name='Oversized Wool Coat', category='Fashion',
                price=329, original_price=459, stock=18, emoji='🧥',
                description='Double-breasted long coat in 70% wool / 30% cashmere blend. Drop-shoulder oversized fit. Notched lapels, horn buttons, two inset pockets and one inner pocket. Lined with satin. Dry-clean only.'),
        Product(seller_id=seller2.id, name='Ribbed Knit Cardigan', category='Fashion',
                price=89,  stock=110, emoji='🧶',
                description='Soft chunky-rib knit in cotton-merino blend. Button-up front, dropped shoulders, balloon sleeves. Layer over a slip dress or under a blazer. Machine-washable on cold.'),
        Product(seller_id=seller2.id, name='Silk Slip Dress', category='Fashion',
                price=159, original_price=229, stock=44, emoji='👗',
                description='100% mulberry silk with bias-cut drape and adjustable spaghetti straps. Cowl neckline. Falls just below the knee. Available in champagne, ivory, dusty rose, sage and onyx.'),
        Product(seller_id=seller2.id, name='Canvas Tote Bag XL', category='Fashion',
                price=49,  stock=140, emoji='👜',
                description='Heavyweight 16oz natural cotton canvas. Reinforced bottom and stitched-down side seams hold up to 12kg. Magnetic snap, interior zip pocket and key clip. Screen-printed minimalist logo.'),
        Product(seller_id=seller2.id, name='Chunky Platform Loafers', category='Fashion',
                price=189, stock=36, emoji='👞',
                description='Smooth leather upper on a 5cm chunky lugged rubber platform. Cushioned memory-foam insole. Penny-loafer styling with metal trim. Available in black, oxblood and cream.'),
        Product(seller_id=seller2.id, name='Vintage-Wash Mom Jeans', category='Fashion',
                price=109, original_price=159, stock=55, emoji='👖',
                description='High-rise mom-fit jeans in non-stretch 100% cotton denim. Faded blue wash with subtle whiskering. Tapered ankle. Five-pocket styling with branded leather patch.'),
        Product(seller_id=seller2.id, name='Pearl Hair Clip Set (6 pcs)', category='Fashion',
                price=29,  stock=200, emoji='💍',
                description='Set of six gold-tone alloy hair clips, three set with faux freshwater pearls and three with crystal accents. Strong hold on thick or fine hair. Comes in a velvet pouch — gift-ready.'),
    ]

    # ── Seller 3 — HomeNest (Home & Living) ───────────────────
    p_home = [
        Product(seller_id=seller3.id, name='Memory Foam Pillow', category='Home',
                price=79,  original_price=129, stock=120, emoji='🛏️',
                description='Contour-cut memory foam supports neck and shoulders. Breathable bamboo-blend cover is removable and machine-washable. CertiPUR-US certified. Stays cool through the night thanks to ventilation channels.'),
        Product(seller_id=seller3.id, name='Linen Bedsheet Set Queen', category='Home',
                price=189, original_price=249, stock=58, emoji='🛌',
                description='Stone-washed pure French linen — fitted sheet, flat sheet and two pillowcases. Gets softer with every wash. Naturally hypoallergenic and temperature-regulating. Twelve earthy colours available.'),
        Product(seller_id=seller3.id, name='Aromatherapy Diffuser', category='Home',
                price=69,  stock=95, emoji='🪔',
                description='300ml ultrasonic essential-oil diffuser with seven LED mood-light colours, three mist modes and auto shut-off. Whisper-quiet. Includes a free starter kit of three pure essential oils.'),
        Product(seller_id=seller3.id, name='Bamboo Cutting Board Set', category='Home',
                price=49,  stock=140, emoji='🍽️',
                description='Set of three organic bamboo boards in graduated sizes. Juice grooves around the edge. Naturally antimicrobial and knife-friendly. Hand-rubbed with food-safe mineral oil before shipping.'),
        Product(seller_id=seller3.id, name='Ceramic French Press 1L', category='Home',
                price=89,  original_price=129, stock=42, emoji='☕',
                description='Hand-glazed stoneware with a stainless-steel double-mesh plunger filter. Retains heat 2× longer than glass presses. Brews 4–6 cups. Dishwasher safe. Available in matte white and clay terracotta.'),
        Product(seller_id=seller3.id, name='LED Desk Lamp with Wireless Charger', category='Home',
                price=109, stock=66, emoji='💡',
                description='Adjustable arm with three colour temperatures and five brightness levels. Built-in 10W Qi wireless pad in the base. Memory function recalls your last setting. USB-A port for a second device.'),
        Product(seller_id=seller3.id, name='Hand-Woven Throw Blanket', category='Home',
                price=99,  stock=80, emoji='🧣',
                description='Chunky boucle-knit throw in 100% recycled wool. 130×170 cm — generous for two on the couch. Fringed ends. Hand-woven in Portugal. Available in oat, charcoal, terracotta and forest.'),
        Product(seller_id=seller3.id, name='Cast Iron Skillet 10"', category='Home',
                price=119, original_price=159, stock=48, emoji='🍳',
                description='Pre-seasoned 10-inch cast iron pan, oven-safe to 260°C. Helper handle for easy lifting. Develops a natural non-stick patina with use. Lifetime guarantee. Hand-wash and oil after each use.'),
        Product(seller_id=seller3.id, name='Modular Shelf Unit', category='Home',
                price=249, original_price=349, stock=22, emoji='📚',
                description='Five-tier industrial shelving in solid acacia and powder-coated steel. 80×30×180 cm. Tool-free snap-together assembly in under ten minutes. Holds up to 30kg per shelf. Anti-tip wall anchor included.'),
        Product(seller_id=seller3.id, name='Scented Soy Candle 8oz', category='Home',
                price=39,  stock=180, emoji='🕯️',
                description='Hand-poured 100% soy wax with phthalate-free fragrance oils. 45-hour burn time. Reusable amber glass jar with wooden wick that crackles softly. Scents: fig & cedar, sea salt, vanilla oud, garden mint.'),
    ]

    # ── Seller 4 — GlowUp Beauty ──────────────────────────────
    p_beauty = [
        Product(seller_id=seller4.id, name='Vitamin C Brightening Serum', category='Beauty',
                price=89,  original_price=149, stock=130, emoji='✨',
                description='20% stabilised L-ascorbic acid with ferulic acid and vitamin E. Brightens dark spots and evens skin tone in 4 weeks. Dropper bottle, 30ml. Vegan, cruelty-free, no parabens or fragrance.'),
        Product(seller_id=seller4.id, name='Hyaluronic Acid Moisturizer', category='Beauty',
                price=69,  stock=140, emoji='💧',
                description='Triple-weight hyaluronic acid penetrates all layers of skin for deep, lasting hydration. Lightweight gel-cream texture absorbs in seconds — no sticky residue. 50ml. Suitable for sensitive skin.'),
        Product(seller_id=seller4.id, name='Matte Liquid Lipstick Set', category='Beauty',
                price=79,  original_price=129, stock=88, emoji='💄',
                description='Set of five long-wear liquid lipsticks in everyday neutral shades. Transfer-proof, kiss-proof, lasts up to 12 hours. Enriched with vitamin E and jojoba oil to prevent drying. Cruelty-free.'),
        Product(seller_id=seller4.id, name='Jade Roller & Gua Sha Set', category='Beauty',
                price=49,  stock=160, emoji='🪨',
                description='Genuine Xiuyan jade in a dual-headed roller plus heart-shaped gua sha stone. Boosts circulation, reduces puffiness and helps serums absorb. Includes a velvet storage pouch and printed ritual guide.'),
        Product(seller_id=seller4.id, name='Retinol Night Cream', category='Beauty',
                price=99,  original_price=159, stock=72, emoji='🌙',
                description='0.5% encapsulated retinol with niacinamide and peptides. Smooths fine lines and refines pores while you sleep. Time-release formula minimises irritation. 50ml in an airless pump for stability.'),
        Product(seller_id=seller4.id, name='Sunscreen SPF 50+ PA++++', category='Beauty',
                price=59,  stock=200, emoji='☀️',
                description='Korean chemical sunscreen with featherlight invisible finish — no white cast, no greasy residue. SPF50+ PA++++ broad-spectrum UVA/UVB protection. Adds a subtle dewy glow. Reef-safe filters. 50ml.'),
        Product(seller_id=seller4.id, name='Eyeshadow Palette 18 Shades', category='Beauty',
                price=89,  stock=64, emoji='🎨',
                description='Eighteen highly-pigmented shades — twelve mattes, four shimmers and two metallic foils. Buttery formula blends seamlessly with minimal fallout. Built-in mirror and dual-ended brush.'),
        Product(seller_id=seller4.id, name='Salon Hair Dryer 1800W', category='Beauty',
                price=199, original_price=299, stock=38, emoji='💇',
                description='Professional-grade brushless motor cuts drying time in half. Ionic technology reduces frizz. Three heat and two speed settings plus cold-shot button. Two concentrator and one diffuser attachment.'),
        Product(seller_id=seller4.id, name='Cleansing Oil 200ml', category='Beauty',
                price=59,  stock=110, emoji='🫒',
                description='Lightweight blend of jojoba, sweet almond and grapeseed oils. Melts away waterproof makeup, sunscreen and impurities — even from sensitive eyes. Emulsifies into a milky lather with water.'),
        Product(seller_id=seller4.id, name='Sheet Mask Variety Pack (10)', category='Beauty',
                price=39,  stock=220, emoji='🧖',
                description='Ten Korean sheet masks across five formulas: hydrating hyaluronic, brightening vitamin C, calming centella, anti-aging collagen and pore-tightening green tea. Biodegradable cellulose sheets.'),
    ]

    # ── Seller 5 — PeakFit Sports ─────────────────────────────
    p_fit = [
        Product(seller_id=seller5.id, name='Yoga Mat 6mm Non-Slip', category='Sports',
                price=89,  original_price=129, stock=110, emoji='🧘',
                description='6mm thick TPE foam — extra cushioning for joints, non-slip on both sides. 183×68 cm. Lightweight at 950g, includes carry strap. Free of PVC, latex and heavy metals. Easy-wipe surface.'),
        Product(seller_id=seller5.id, name='Adjustable Dumbbells 24kg Pair', category='Sports',
                price=599, original_price=899, stock=20, emoji='🏋️',
                description='Quick-swap dial adjusts from 2.5kg to 24kg per dumbbell in 2.5kg increments. Replaces 14 traditional dumbbells. Compact storage tray included. Plates are coated in matte rubber to protect floors.'),
        Product(seller_id=seller5.id, name='Resistance Band Set (5 levels)', category='Sports',
                price=49,  stock=180, emoji='💪',
                description='Five colour-coded latex tubes from 5lb to 50lb resistance. Includes two soft-grip handles, two ankle straps, door anchor, and a printed exercise booklet. Carry bag included.'),
        Product(seller_id=seller5.id, name='Cycling Bib Shorts', category='Sports',
                price=149, original_price=219, stock=42, emoji='🚴',
                description='Italian Lycra Power compression fabric with a multi-density chamois pad rated for 5-hour rides. Laser-cut leg grippers — no silicone irritation. Mesh upper for ventilation. Reflective rear logo.'),
        Product(seller_id=seller5.id, name='Foam Roller High-Density', category='Sports',
                price=39,  stock=140, emoji='🧱',
                description='High-density EPP foam roller, 33×14 cm. Firm enough for deep tissue work without losing its shape. Lightweight at 350g — easy to take to the gym. Available in black, blue and pink.'),
        Product(seller_id=seller5.id, name='Hiking Backpack 30L', category='Sports',
                price=189, original_price=259, stock=50, emoji='🎒',
                description='Lightweight ripstop nylon with welded seams — waterproof to IPX4. Ventilated mesh back panel. Hydration bladder compatible. Padded hip belt with two zip pockets. Daisy-chain attachment loops.'),
        Product(seller_id=seller5.id, name='Boxing Gloves 12oz', category='Sports',
                price=129, stock=58, emoji='🥊',
                description='Hand-stitched genuine cowhide leather with multi-layer foam padding. Long Velcro cuff for wrist support. Mesh palm for ventilation. 12oz suits training and bag work. Pair with hand wraps.'),
        Product(seller_id=seller5.id, name='Smart Jump Rope', category='Sports',
                price=59,  stock=100, emoji='🪢',
                description='Built-in sensors count jumps, calories and time. Pairs with the PeakFit app via Bluetooth. Adjustable steel cable up to 2.8m. Replaceable AAA battery lasts six months. Ball-bearing handles spin smoothly.'),
        Product(seller_id=seller5.id, name='Trail Running Shoes', category='Sports',
                price=229, original_price=339, stock=30, emoji='👟',
                description='Aggressive 5mm lugs on a sticky rubber outsole grip mud, rock and roots. Rock plate protects the forefoot. Quick-pull lacing system. Reinforced toe cap. Drains and dries fast after stream crossings.'),
        Product(seller_id=seller5.id, name='Protein Bar Variety Box (24)', category='Food',
                price=99,  original_price=149, stock=120, emoji='🍫',
                description='Twenty-four bars across six flavours — chocolate brownie, salted caramel, peanut butter, cookies & cream, vanilla almond and mocha. 20g protein, 3g sugar, 200 cal each. Gluten-free.'),
    ]

    new_products = p_seoul + p_home + p_beauty + p_fit
    db.session.add_all(new_products)
    db.session.flush()

    # ── Orders + reviews for new products ─────────────────────
    # Spread reviewers across the catalog so seller reputations are built up.
    review_plan = [
        # Seoul Style (Fashion)
        (p_seoul[0], [(a, 5, "Such a flattering fit and the denim has a great vintage feel. Pairs with everything in my wardrobe.", 22),
                       (b, 4, "Lovely cut. Slightly snug on the bust but the cropped length is perfect.", 17),
                       (c, 5, "Quality denim, beautiful wash. Got a ton of compliments already.", 11)]),
        (p_seoul[1], [(d, 5, "Pleats stayed crisp after washing — so often that's the part that fails. Love it.", 20),
                       (e, 4, "Cute and comfy, runs slightly small so size up if between sizes.", 13)]),
        (p_seoul[2], [(f, 5, "True linen quality, breathes like a dream in the heat. Wide leg drape is gorgeous.", 19),
                       (g, 5, "Best summer pants I own. Wrinkles, sure, but that's just how linen looks.", 12)]),
        (p_seoul[3], [(h, 5, "Stunning coat — the wool blend feels luxurious and the cut is so flattering.", 28),
                       (iv, 4, "Beautifully made. Heavy enough for cold winters here. Worth the price.", 18)]),
        (p_seoul[4], [(j, 5, "Cosiest cardigan I own. The button details are lovely and the knit is thick.", 25),
                       (a, 4, "Soft and warm, the buttons feel solid. Sleeves are quite long which I love.", 14)]),
        (p_seoul[5], [(b, 5, "Pure silk for this price is unreal. The drape is exactly what slip dresses should be.", 21),
                       (c, 5, "Gorgeous dress, fits true to size. Already worn it to two weddings.", 10)]),
        (p_seoul[6], [(d, 5, "Holds an absurd amount of groceries. The reinforced bottom does not joke around.", 16),
                       (e, 4, "Big sturdy bag, exactly what I needed for the farmer's market run.", 9)]),
        (p_seoul[7], [(f, 5, "Comfortable from day one, no break-in needed. The platform is the perfect height.", 24),
                       (g, 4, "Stylish and well-made. Slightly heavy but very durable feel.", 15)]),
        (p_seoul[8], [(h, 5, "Best mom jeans I have tried — proper high rise, no stretch but still comfy.", 26),
                       (iv, 4, "Lovely vintage wash, fits as expected. Slight shrinkage after first wash.", 13)]),
        (p_seoul[9], [(j, 5, "Adorable set, the pearls look much more expensive than they are.", 11),
                       (a, 5, "Strong grip on my thick hair. The velvet pouch is a nice touch.", 7)]),

        # HomeNest (Home)
        (p_home[0],  [(b, 5, "Game-changer for my neck pain. Wake up without stiffness now.", 30),
                       (c, 5, "Perfect height and support — and stays cool unlike my old memory foam.", 22),
                       (d, 4, "Comfortable and well-made. Took two nights to get used to it.", 14)]),
        (p_home[1],  [(e, 5, "Linen sheets are a revelation — cool in summer, warm in winter. Getting softer too.", 27),
                       (f, 5, "Worth every yuan. Hotel-quality linen at home.", 18)]),
        (p_home[2],  [(g, 4, "Quiet and pretty. The included oils smell genuine, not synthetic.", 21),
                       (h, 5, "Mist runs for hours and the colour cycling is calming. Adds a lot to the room.", 12)]),
        (p_home[3],  [(iv, 5, "Beautifully made boards. The juice grooves actually contain everything — no mess.", 23),
                       (j, 4, "Solid bamboo, light enough to handle easily. The smallest one is great for fruit.", 13)]),
        (p_home[4],  [(a, 5, "Coffee stays piping hot for ages. The ceramic is hefty and feels premium.", 19),
                       (b, 5, "Best French press I have used. Mesh filter really blocks the grit.", 9)]),
        (p_home[5],  [(c, 5, "The wireless charger in the base is genius. One less cable on my desk.", 17),
                       (d, 4, "Bright, well-built lamp. The memory function is more useful than I expected.", 8)]),
        (p_home[6],  [(e, 5, "Gorgeous throw, super warm and weighty. Looks expensive on the couch.", 25),
                       (f, 4, "Thick chunky knit, perfect for movie nights. A bit of shedding initially.", 14)]),
        (p_home[7],  [(g, 5, "This thing will outlive me. Sears steaks like a steakhouse grill.", 24),
                       (h, 4, "Heavy as expected, seasoning was solid out of the box. Develops a great patina.", 11)]),
        (p_home[8],  [(iv, 5, "Sturdy shelves, took us 15 minutes to put together. Holds my book collection easily.", 20),
                       (j, 4, "Nice industrial look. Wood quality is better than I expected at this price.", 10)]),
        (p_home[9],  [(a, 5, "Fig & cedar is incredible — smells like an upscale boutique. Burns evenly.", 18),
                       (b, 5, "The wooden wick crackle is so cozy. Already ordered two more.", 6)]),

        # GlowUp Beauty
        (p_beauty[0], [(c, 5, "Skin texture noticeably improved after three weeks. Dark spots are fading.", 28),
                        (d, 5, "Best vitamin C serum I have tried — and I have tried many. Absorbs fast.", 19),
                        (e, 4, "Definitely brightens, slight tingle at first but my skin adjusted quickly.", 11)]),
        (p_beauty[1], [(f, 5, "Plumps my skin instantly. Layers well under makeup with zero pilling.", 24),
                        (g, 5, "Hydration that actually lasts all day. Holy grail product.", 13)]),
        (p_beauty[2], [(h, 5, "Stays on through coffee, lunch, and meetings. The neutral shades are wearable everywhere.", 26),
                        (iv, 4, "Long-lasting and comfortable, only the lightest shade is a tiny bit drying.", 14)]),
        (p_beauty[3], [(j, 5, "Reduced morning puffiness within a week. The jade feels gorgeous and cool.", 22),
                        (a, 5, "Gua sha has become a daily ritual. The included guide is genuinely useful.", 9)]),
        (p_beauty[4], [(b, 5, "No irritation and visible smoothing of fine lines in a month. Best retinol I've found.", 30),
                        (c, 4, "Gentle and effective. The airless pump keeps it fresh.", 16)]),
        (p_beauty[5], [(d, 5, "Invisible finish — finally a sunscreen I'll actually wear every day.", 21),
                        (e, 5, "Sits beautifully under makeup. No white cast on my darker skin tone.", 10)]),
        (p_beauty[6], [(f, 5, "Pigment is unreal for the price. The mattes blend like a dream.", 18),
                        (g, 4, "Great variety of wearable shades. The shimmers are stunning.", 8)]),
        (p_beauty[7], [(h, 5, "Cuts my drying time literally in half. Hair is shinier and less frizzy.", 26),
                        (iv, 4, "Powerful and quiet for its size. Wish it had more colour options.", 13)]),
        (p_beauty[8], [(j, 5, "Removes a full face of waterproof makeup effortlessly. No tugging on eyes.", 17),
                        (a, 4, "Pleasant scent, emulsifies well. A pump bottle would be even better.", 7)]),
        (p_beauty[9], [(b, 5, "Variety pack is perfect for figuring out which formula your skin loves.", 12),
                        (c, 5, "Great value. The hydrating ones leave my skin glowing the next morning.", 5)]),

        # PeakFit Sports
        (p_fit[0],    [(d, 5, "Thick, grippy and odor-free. Holds knee balance poses without slipping.", 24),
                        (e, 4, "Great mat for the price. A bit of an initial smell that aired out in two days.", 15)]),
        (p_fit[1],    [(f, 5, "Replaces a whole rack of dumbbells. Dial mechanism feels rock solid after months of use.", 27),
                        (g, 5, "Worth every yuan for a home gym. Swaps are fast — no flow break between sets.", 16)]),
        (p_fit[2],    [(h, 5, "Great range of resistance, the door anchor works flawlessly. Use them every day.", 22),
                        (iv, 4, "Solid set for travel. The booklet is genuinely helpful for routine ideas.", 12)]),
        (p_fit[3],    [(j, 5, "The chamois is the most comfortable I have ridden in. Five hours, zero soreness.", 25),
                        (a, 4, "Premium feel and proper compression. Sizing runs European — order up if in doubt.", 14)]),
        (p_fit[4],    [(b, 5, "Firm enough for real release on my IT band without crumbling like cheap rollers.", 19),
                        (c, 4, "Light and tough. Perfect after-leg-day tool.", 8)]),
        (p_fit[5],    [(d, 5, "Survived a rainy three-day hike with zero leaks. Suspension system is comfortable loaded.", 23),
                        (e, 5, "Lightweight but holds everything I need. The hip pockets are surprisingly roomy.", 11)]),
        (p_fit[6],    [(f, 5, "Genuine leather, beautifully stitched. Wrist support is excellent for bag work.", 20),
                        (g, 4, "Comfortable padding, fits true to size. Smells like real leather — love it.", 10)]),
        (p_fit[7],    [(h, 5, "App syncing is seamless. Makes my morning rope sessions way more engaging.", 17),
                        (iv, 4, "Light handles, smooth spin. Counting feels accurate against my phone count.", 9)]),
        (p_fit[8],    [(j, 5, "Glued to wet rocks on a recent scramble. Lacing system is fast and stays put.", 21),
                        (a, 5, "Brilliant grip on technical terrain. Drains well after a stream crossing.", 13)]),
        (p_fit[9],    [(b, 5, "Tastes like dessert but the macros are legit. Salted caramel is my pre-workout fix.", 15),
                        (c, 4, "Big variety, none of the flavours are bad. A bit chewy at room temp but warm them slightly and they're perfect.", 7)]),
    ]

    # Create orders for each reviewer + product so the bought-check passes,
    # then add the actual review.
    for product, planned_reviews in review_plan:
        for (reviewer, rating, comment, days_ago) in planned_reviews:
            make_order(reviewer, product, 1, days_ago + 1)
            rev(reviewer, product, rating, comment, days_ago)

    # ── Top-up reviews: ensure every product has 10 reviews ───
    # Uses category-aware templates so reviews stay realistic.
    review_templates = {
        'Electronics': [
            (5, "Performs exactly as advertised. Setup was effortless and it has held up perfectly."),
            (4, "Solid build quality and reliable so far. Nothing fancy, but it does the job well."),
            (5, "Great value for the price. Compared with pricier alternatives — couldn't see the difference."),
            (5, "Honestly impressed. The features I cared about all work, the rest are a nice bonus."),
            (4, "Works as expected. Instructions could be clearer but nothing a quick search couldn't solve."),
            (5, "Replaces three older gadgets I used to keep around. One less thing on my desk."),
            (4, "Fast shipping, well packaged. The product itself is reliable — no complaints after a month."),
            (3, "Decent product. A few small annoyances I won't bother returning over, but worth knowing."),
            (5, "Bought a second one for the office. That tells you everything you need to know."),
            (4, "Battery and performance live up to the listing. Would recommend to a friend."),
            (5, "Sleek design and surprisingly intuitive. Use it daily now."),
            (5, "Great quality, especially considering the discount. Snapped it up and glad I did."),
        ],
        'Fashion': [
            (5, "Fits true to size and the fabric is much nicer in person. Already wearing it weekly."),
            (5, "Beautiful piece — clean stitching and the colour matches the photos exactly."),
            (4, "Lovely material and cut. Slightly snug at first but loosened up after a wash."),
            (5, "Get compliments every time I wear it. Quality you'd expect from a much pricier brand."),
            (5, "Versatile — dressed up or down, it works. A total wardrobe staple now."),
            (4, "Solid quality for the price. Photos do it justice. Buy with confidence."),
            (4, "Nice fabric and stitching. Sizing chart was spot on for me."),
            (5, "Surprised by how flattering the cut is. Ordered a second colour the next day."),
            (3, "Fits well but the colour is a touch lighter than expected. Otherwise nice."),
            (5, "Genuinely well-made. Strong fabric, clean seams, no loose threads."),
            (5, "Comfortable from day one, holds shape after washing. Highly recommend."),
            (4, "Lovely piece. Took a week to arrive but worth the wait."),
        ],
        'Home': [
            (5, "Made our place feel instantly cosier. Build quality is reassuringly solid."),
            (5, "Looks gorgeous in person — even better than the photos. Sturdy too."),
            (4, "Nicely made. Took a few minutes to set up and has been faultless since."),
            (5, "Replaced an old cheaper version — the difference is night and day."),
            (4, "Good value. Materials feel premium for the price point."),
            (5, "Already recommended to two friends. Genuinely useful daily."),
            (5, "Beautiful design and proper craftsmanship. Worth every yuan."),
            (4, "Solid product, packaging was excellent. Arrived without a scratch."),
            (5, "Just what I was looking for. Fits perfectly in my space and works flawlessly."),
            (3, "It's fine. Does what it says. Nothing wow but no complaints either."),
            (5, "Better than expected. Heavier and more substantial than the photos suggest."),
            (4, "Lovely addition to the kitchen / living room. Easy to clean."),
        ],
        'Beauty': [
            (5, "Skin feels noticeably better after two weeks. Will repurchase."),
            (5, "Gentle formula, no irritation even on my sensitive skin. Pleasant texture too."),
            (4, "Works as described. Takes a few weeks for visible results but worth the patience."),
            (5, "Long-lasting and the packaging is so pretty. Looks great on my vanity."),
            (5, "Holy grail status. Tried many alternatives and keep coming back to this one."),
            (4, "Decent product, nice scent, not too overpowering. Absorbs well."),
            (5, "Honestly the best I've used in this category. Saw changes within days."),
            (3, "Okay product. Didn't blow me away but didn't disappoint either."),
            (5, "Glowy skin every time. Already on my second bottle."),
            (4, "Lightweight, non-greasy, easy to apply. Good for daily routine."),
            (5, "Vegan and cruelty-free which I appreciate. Effective too — bonus."),
            (5, "Lasted way longer than I expected. Brilliant value."),
        ],
        'Sports': [
            (5, "Comfortable from the first use, no break-in needed. Holds up to daily training."),
            (5, "Build quality is excellent. Survived a few drops and still looks new."),
            (4, "Does the job well. Sizing was accurate, comfortable to use."),
            (5, "Noticeable improvement to my workouts. Wish I'd bought it sooner."),
            (4, "Solid gear at a fair price. Holds up to regular gym use."),
            (5, "Lightweight but durable — exactly what I needed for travel days."),
            (5, "Best in this category I've owned. Considering buying a second as backup."),
            (4, "Nice product. The included accessories are a useful bonus."),
            (5, "Heavy-duty feel. Already used it a dozen times — zero issues."),
            (3, "Functional. A few minor design quirks, but performs as advertised."),
            (5, "Highly recommended for anyone serious about training at home."),
            (5, "Beautifully made. Attention to detail is rare at this price point."),
        ],
        'Food': [
            (5, "Surprisingly tasty and a great mix of flavours. Will reorder."),
            (5, "Quality ingredients and the packaging keeps everything fresh."),
            (4, "Tasty and convenient. Some flavours stand out more than others."),
            (5, "Generous portion sizes. Genuinely satisfying — not just empty calories."),
            (4, "Good variety. Most are great, a couple are just okay — still a win overall."),
            (5, "My new go-to. Stocking up before they go out of stock."),
            (5, "Sent as a gift — the recipient loved it. Beautiful presentation."),
            (3, "Decent. A bit pricier than supermarket alternatives but the quality is there."),
            (5, "Big flavours, none of them taste cheap or artificial. Pleasantly surprised."),
            (4, "Solid snack pack. The protein content is real, not just marketing."),
            (5, "Travels well, doesn't melt or crumble. Perfect for office or gym bag."),
            (5, "Honestly delicious. Have already ordered twice this month."),
        ],
    }
    generic_templates = review_templates['Home']
    all_reviewers = reviewers  # 10 reviewers (a..j)

    db.session.flush()  # make existing reviews visible to the query below

    all_products_now = products + new_products
    for p in all_products_now:
        existing_user_ids = {r.user_id for r in Review.query.filter_by(product_id=p.id).all()}
        pool = review_templates.get(p.category, generic_templates)
        slot = 0
        for r in all_reviewers:
            if r.id in existing_user_ids:
                continue
            rating, comment = pool[(p.id + slot) % len(pool)]
            days_ago = 40 + slot * 3  # 40, 43, 46, …
            make_order(r, p, 1, days_ago + 1)
            rev(r, p, rating, comment, days_ago)
            slot += 1

    # ── Seller reviews (overall shop reputation) ──────────────
    def srev(reviewer, target_seller, rating, comment, days_ago):
        db.session.add(SellerReview(
            seller_id=target_seller.id, user_id=reviewer.id,
            username=reviewer.username, rating=rating, comment=comment,
            created_at=now - timedelta(days=days_ago),
        ))

    # TechStore Pro
    srev(a, seller, 5, "Fast shipping and everything arrived perfectly packaged. Easy returns process too.", 20)
    srev(b, seller, 5, "Trusted shop — bought multiple electronics here, always genuine and as described.", 18)
    srev(c, seller, 4, "Reliable seller. Customer service replied to my question within an hour.", 14)
    srev(d, seller, 5, "Consistent quality across all their products. My go-to for tech accessories.", 9)
    srev(e, seller, 4, "Great prices and fast delivery. One package was slightly delayed but they kept me updated.", 5)

    # Seoul Style Co.
    srev(f, seller2, 5, "Beautiful packaging and the quality matches the price. Sizing chart is accurate.", 22)
    srev(g, seller2, 5, "Genuinely curated fashion — feels like a boutique. Adore everything I've ordered.", 17)
    srev(h, seller2, 4, "Lovely products but shipping took longer than expected. Worth the wait.", 12)
    srev(iv, seller2, 5, "Customer service helped me find the right size — super friendly.", 7)

    # HomeNest
    srev(j, seller3, 5, "Everything for my apartment refresh came from here. Quality is consistent.", 25)
    srev(a, seller3, 5, "Sturdy, well-packaged home goods. Their candles alone are worth a five-star.", 16)
    srev(b, seller3, 4, "Solid seller. The shelf I ordered had a small scratch but they sent a replacement panel quickly.", 10)
    srev(c, seller3, 5, "Trustworthy shop with great taste. Highly recommend.", 4)

    # GlowUp Beauty
    srev(d, seller4, 5, "All products genuine — I checked batch codes. Skin has never looked better.", 24)
    srev(e, seller4, 5, "Free samples in every order is a lovely touch. Real beauty experts.", 14)
    srev(f, seller4, 4, "Good selection and reliable shipping. Wish they offered subscriptions.", 8)
    srev(g, seller4, 5, "Best beauty shop on ShopHub. Skincare advice in their listings is actually helpful.", 3)

    # PeakFit Sports
    srev(h, seller5, 5, "Heavy items shipped fast and well-protected. The dumbbells arrived perfectly.", 21)
    srev(iv, seller5, 5, "Quality gear at fair prices. Customer support answered my training question with a real answer, not a script.", 13)
    srev(j, seller5, 4, "Solid seller for home gym essentials. A few items run a bit small.", 9)
    srev(a, seller5, 5, "Have ordered six times now. Never a single problem. Trustworthy and fast.", 5)

    # ── Announcements ─────────────────────────────────────────
    announcements = [
        Announcement(title='🎉 Welcome to ShopHub Spring Festival 2026',
                     content='Discover thousands of curated products with exclusive Spring discounts up to 60% off. Join us for our biggest sale of the year!',
                     created_at=now - timedelta(days=2)),
        Announcement(title='🤖 Meet ShopBot — Our New AI Shopping Assistant',
                     content='Click the chat button in the bottom-right corner to get personalised recommendations, see reviews, and even check out — all through conversation.',
                     created_at=now - timedelta(days=1)),
        Announcement(title='🛡️ Buyer Protection Program Upgraded',
                     content='Every purchase on ShopHub now comes with a 30-day money-back guarantee and free returns on all eligible items.',
                     created_at=now - timedelta(days=5)),
        Announcement(title='🏪 New Seller Onboarding Now Free',
                     content='Sign up as a seller this month and pay zero commission for your first 90 days. Reach millions of buyers worldwide.',
                     created_at=now - timedelta(days=8)),
        Announcement(title='⚡ Flash Sale Every Friday',
                     content='Mark your calendars — every Friday at 8 PM we drop fresh deals on electronics, fashion and home goods. Limited stock available.',
                     created_at=now - timedelta(days=12)),
        Announcement(title='📱 Mobile App Coming Soon',
                     content='ShopHub mobile app for iOS and Android launches in Q3 2026. Pre-register now to receive ¥50 in app credit on launch day.',
                     created_at=now - timedelta(days=18)),
    ]
    db.session.add_all(announcements)
    db.session.commit()
