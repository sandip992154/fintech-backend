const productList = {
  status: "success",
  message: "Product list fetched successfully",
  data: {
    products: [
      {
        id: "PROD001",
        title: "Apple iPhone 14 Pro Max (256GB, Deep Purple)",
        brand: "Apple",
        category: "Mobiles",
        comment:
          "The iPhone 14 Pro Max offers an exceptional camera system, stunning display, and robust performance, making it a top-tier choice for smartphone enthusiasts.",
        vendors: {
          Amazon: {
            price: 139999,
            discountPrice: 134999,
            rating: 4.8,
            affiliateLink:
              "https://affiliate.example.com/product/PROD001/Amazon",
            offers: [
              "₹5,000 instant discount on ICICI Credit Cards",
              "Exchange bonus up to ₹12,000",
              "No Cost EMI for 6 months",
            ],
          },
          Flipkart: {
            price: 139999,
            discountPrice: 132499,
            rating: 4.7,
            affiliateLink:
              "https://affiliate.example.com/product/PROD001/Flipkart",
            offers: [
              "₹7,000 Off on Axis Bank Cards",
              "Flat ₹1,000 Off with Flipkart SuperCoins",
              "3-month screen protection included",
            ],
          },
          Croma: {
            price: 139900,
            discountPrice: 135900,
            rating: 4.6,
            affiliateLink:
              "https://affiliate.example.com/product/PROD001/Croma",
            offers: [
              "Up to ₹6,000 cashback on HDFC Bank Credit Cards",
              "Extended warranty plans available",
            ],
          },
          JioMart: {
            price: 139900,
            discountPrice: 133900,
            rating: 4.5,
            affiliateLink:
              "https://affiliate.example.com/product/PROD001/JioMart",
            offers: [
              "₹4,000 instant discount on SBI Credit Cards",
              "No Cost EMI for 9 months",
            ],
          },
          "Vijay Sales": {
            price: 139900,
            discountPrice: 136900,
            rating: 4.7,
            affiliateLink:
              "https://affiliate.example.com/product/PROD001/VijaySales",
            offers: [
              "₹3,000 store credit on next purchase",
              "Free screen protector and case",
            ],
          },
        },
        image: {
          thumbnail: "https://example.com/images/iphone14pro.jpg",
          urls: [
            "https://example.com/images/iphone14pro.jpg",
            "https://example.com/images/iphone14pro-2.jpg",
            "https://example.com/images/iphone14pro-3.jpg",
          ],
        },
        features: {
          type: "mobile",
          details: {
            Design: {
              Width: "77.6 mm",
              Thickness: "7.85 mm",
              Weight: "240 g",
              Material:
                "Ceramic Shield front, Textured matte glass back and stainless steel design",
              "Water Resistance":
                "IP68 (maximum depth of 6 meters up to 30 minutes)",
            },
            Display: {
              "Screen Size": "6.7 inch",
              "Screen Resolution": "2796 x 1290 pixels",
              "Display Type": "Super Retina XDR OLED",
              "Pixel Density": "460 ppi",
              "Touch Screen": "Yes",
              Brightness: "Up to 2000 nits peak brightness (outdoor)",
              "Refresh Rate":
                "ProMotion technology with adaptive refresh rates up to 120Hz",
              Features:
                "Dynamic Island, Always-On display, HDR display, True Tone, Haptic Touch",
            },
            "Network & Connectivity": {
              "Sim Size": "Nano SIM + eSIM",
              "Network Support": "5G, 4G, 3G, 2G",
              "Wi-Fi": "Yes, Wi-Fi 6 (802.11ax) with 2x2 MIMO",
              "Wi-Fi Features": "Mobile Hotspot",
              Bluetooth: "Yes, v5.3",
              GPS: "Yes, with GLONASS, Galileo, QZSS, and BeiDou",
              NFC: "Yes, with reader mode",
              "USB Connectivity": "Lightning Port",
            },
            Performance: {
              Processor: "A16 Bionic Chip",
              Cores: "6-core CPU with 2 performance and 4 efficiency cores",
              GPU: "5-core GPU",
              "Neural Engine": "16-core Neural Engine",
              "Operating System": "iOS 16",
            },
            Camera: {
              "Rear Camera":
                "48MP Main (f/1.78), 12MP Ultra Wide (f/2.2), 12MP Telephoto (f/2.8)",
              "Front Camera": "12MP TrueDepth Camera (f/1.9) with autofocus",
              "Video Recording":
                "4K at 24/25/30/60 fps, 1080p HD at 25/30/60 fps, Cinematic mode up to 4K HDR at 30 fps, Action mode up to 2.8K at 60 fps",
              "Camera Features":
                "Photonic Engine, Deep Fusion, Smart HDR 4, Portrait mode with advanced bokeh and Depth Control, Portrait Lighting, Night mode, Macro photography, Apple ProRAW",
            },
            Battery: {
              "Battery Type": "Built-in rechargeable lithium-ion battery",
              "Video Playback": "Up to 29 hours",
              "Audio Playback": "Up to 95 hours",
              Charging:
                "MagSafe wireless charging up to 15W, Qi wireless charging up to 7.5W, Fast-charge capable (up to 50% charge in around 30 minutes with 20W adapter or higher)",
            },
            Sensors: {
              "Face ID": "Yes",
              Barometer: "Yes",
              Gyro: "High dynamic range gyro",
              Accelerometer: "High-g accelerometer",
              "Proximity Sensor": "Yes",
              "Ambient Light Sensor": "Dual ambient light sensors",
            },
            Audio: {
              Speakers: "Stereo speakers",
              Microphones: "Built-in microphones",
            },
          },
        },
        tags: [
          "Smartphone",
          "5G",
          "iOS",
          "Premium",
          "Flagship",
          "Photography",
          "High Performance",
        ],
      },
      {
        id: "PROD002",
        title: "Dell Inspiron 15 5000 (11th Gen i5, 8GB, 512GB SSD)",
        brand: "Dell",
        category: "Laptops",
        comment:
          "A reliable and efficient laptop for everyday tasks and moderate productivity, offering good value for its features.",
        vendors: {
          Amazon: {
            price: 64999,
            discountPrice: 59999,
            rating: 4.3,
            affiliateLink:
              "https://affiliate.example.com/product/PROD002/Amazon",
            offers: [
              "₹5,000 Off on ICICI Bank Credit Cards",
              "EMI starting from ₹2,499/month",
            ],
          },
          Flipkart: {
            price: 65999,
            discountPrice: 61999,
            rating: 4.2,
            affiliateLink:
              "https://affiliate.example.com/product/PROD002/Flipkart",
            offers: [
              "₹4,000 Off on HDFC Bank Debit Cards",
              "No Cost EMI for 3 months",
            ],
          },
          "Dell India": {
            price: 66000,
            discountPrice: 60500,
            rating: 4.4,
            affiliateLink:
              "https://affiliate.example.com/product/PROD002/DellIndia",
            offers: ["Free backpack and mouse", "1-year extended warranty"],
          },
          Croma: {
            price: 65500,
            discountPrice: 60999,
            rating: 4.3,
            affiliateLink:
              "https://affiliate.example.com/product/PROD002/Croma",
            offers: [
              "Up to ₹3,000 cashback on Axis Bank Credit Cards",
              "Accidental damage protection plan",
            ],
          },
          "Vijay Sales": {
            price: 64500,
            discountPrice: 59500,
            rating: 4.3,
            affiliateLink:
              "https://affiliate.example.com/product/PROD002/VijaySales",
            offers: [
              "₹2,500 instant discount on Kotak Bank Cards",
              "Exchange offer for old laptops",
            ],
          },
        },
        image: {
          thumbnail: "https://example.com/images/dell-inspiron15.jpg",
          urls: [
            "https://example.com/images/dell-inspiron15.jpg",
            "https://example.com/images/dell-inspiron15-2.jpg",
          ],
        },
        features: {
          type: "laptop",
          details: {
            Display: {
              "Screen Size": "15.6 inch",
              Resolution: "1920 x 1080 pixels",
              "Display Type": "FHD Anti-Glare LED",
              Brightness: "220 nits",
              Bezel: "Narrow Border Display",
            },
            Performance: {
              Processor: "Intel Core i5 11th Gen (1135G7)",
              RAM: "8GB DDR4 (3200MHz, expandable up to 16GB)",
              Storage: "512GB NVMe SSD",
              "Operating System": "Windows 11 Home (with lifetime validity)",
              Graphics: "Intel Iris Xe Graphics (Integrated)",
            },
            Connectivity: {
              "Wi-Fi": "Yes, Wi-Fi 5 (802.11ac)",
              Bluetooth: "Yes, v5.0",
              Ports:
                "2x USB 3.2 Gen 1 Type-A, 1x USB 2.0 Type-A, 1x HDMI 1.4, 1x Audio Jack, 1x SD Card Reader",
              Ethernet: "No",
            },
            Audio: {
              Speakers: "Stereo speakers with Waves MaxxAudio Pro",
              Microphone: "Integrated dual-array microphone",
            },
            Input: {
              Keyboard:
                "Full-size spill-resistant keyboard with numeric keypad",
              Touchpad: "Multi-touch gesture-enabled precision touchpad",
            },
            Battery: {
              "Battery Type": "3-cell, 41 Whr Integrated",
              "Battery Life": "Up to 7 hours (varied usage)",
              Charging: "65W AC Adapter",
            },
            Dimensions: {
              Weight: "1.78 kg",
              Thickness: "18.9 mm",
              Width: "358.5 mm",
              Depth: "235.56 mm",
            },
            Webcam: {
              Resolution: "720p HD",
              Features:
                "Integrated widescreen HD (720p) webcam with Digital Microphone",
            },
          },
        },
        tags: [
          "Laptop",
          "Windows",
          "Office Included",
          "Everyday Use",
          "Productivity",
          "Student Laptop",
        ],
      },
      {
        id: "GEN003",
        title: "Sample Product for Electronics Devices",
        brand: "GenericBrand",
        category: "Electronics Devices",
        comment:
          "A versatile electronic device suitable for various needs, offering a good balance of features and affordability.",
        vendors: {
          Amazon: {
            price: 4999,
            discountPrice: 3999,
            rating: 4.0,
            affiliateLink:
              "https://affiliate.example.com/product/GEN003/Amazon",
            offers: ["₹500 Off", "Free Shipping"],
          },
          "Reliance Digital": {
            price: 5299,
            discountPrice: 4199,
            rating: 3.9,
            affiliateLink:
              "https://affiliate.example.com/product/GEN003/RelianceDigital",
            offers: [
              "10% cashback on select credit cards",
              "Extended warranty available",
            ],
          },
          JioMart: {
            price: 5199,
            discountPrice: 4099,
            rating: 3.9,
            affiliateLink:
              "https://affiliate.example.com/product/GEN003/JioMart",
            offers: [
              "Extra 5% off on UPI payments",
              "No-cost EMI on Bajaj Finserv",
            ],
          },
        },
        image: {
          thumbnail: "https://example.com/images/generic.jpg",
          urls: ["https://example.com/images/generic.jpg"],
        },
        features: {
          type: "generic",
          details: {
            General: {
              Model: "GEN-ELE-2025",
              Description: "Placeholder specs for Electronics Devices category",
              Connectivity: "Bluetooth 5.0, USB-C",
              "Battery Life": "Up to 8 hours",
              "Color Options": "Black, White, Blue",
              Weight: "200g",
            },
          },
        },
        tags: [
          "Electronics",
          "Generic",
          "Electronics Devices",
          "Portable",
          "Gadget",
        ],
      },
      {
        id: "GEN004",
        title: "Sample Product for Computer & Laptop",
        brand: "GenericBrand",
        category: "Computer & Laptop",
        comment:
          "An entry-level computing solution for basic tasks, ideal for students or home users.",
        vendors: {
          Amazon: {
            price: 5499,
            discountPrice: 4499,
            rating: 4.2,
            affiliateLink:
              "https://affiliate.example.com/product/GEN004/Amazon",
            offers: ["₹500 Off", "Free Shipping"],
          },
          "Vijay Sales": {
            price: 5699,
            discountPrice: 4699,
            rating: 4.1,
            affiliateLink:
              "https://affiliate.example.com/product/GEN004/VijaySales",
            offers: [
              "Bundle offer with essential accessories",
              "Easy EMI options",
            ],
          },
          Flipkart: {
            price: 5599,
            discountPrice: 4599,
            rating: 4.0,
            affiliateLink:
              "https://affiliate.example.com/product/GEN004/Flipkart",
            offers: [
              "₹300 off on Prepaid orders",
              "Free antivirus subscription for 1 year",
            ],
          },
        },
        image: {
          thumbnail: "https://example.com/images/generic.jpg",
          urls: ["https://example.com/images/generic.jpg"],
        },
        features: {
          type: "generic",
          details: {
            General: {
              Model: "GEN-COM-2025",
              Description: "Placeholder specs for Computer & Laptop category",
              Processor: "Entry-level Dual-Core",
              RAM: "4GB DDR3",
              Storage: "128GB SSD",
              "Operating System": "Windows 10 S",
              "Screen Size": "14 inch",
              Webcam: "Integrated 720p Webcam",
            },
          },
        },
        tags: [
          "Electronics",
          "Generic",
          "Computer & Laptop",
          "Budget-friendly",
          "Basic Computing",
        ],
      },
      {
        id: "GEN005",
        title: "Sample Product for Laptop Accessories",
        brand: "GenericBrand",
        category: "Laptop Accessories",
        comment:
          "Essential accessories to enhance your laptop experience, offering convenience and protection.",
        vendors: {
          Amazon: {
            price: 5999,
            discountPrice: 4999,
            rating: 4.0,
            affiliateLink:
              "https://affiliate.example.com/product/GEN005/Amazon",
            offers: ["₹500 Off", "Free Shipping"],
          },
          ShopClues: {
            price: 6199,
            discountPrice: 5099,
            rating: 3.8,
            affiliateLink:
              "https://affiliate.example.com/product/GEN005/ShopClues",
            offers: ["Bulk purchase discounts", "Cash on delivery available"],
          },
          Croma: {
            price: 6099,
            discountPrice: 5049,
            rating: 3.9,
            affiliateLink: "https://affiliate.example.com/product/GEN005/Croma",
            offers: [
              "Assured gift on purchase above ₹5000",
              "EMI options available",
            ],
          },
        },
        image: {
          thumbnail: "https://example.com/images/generic.jpg",
          urls: ["https://example.com/images/generic.jpg"],
        },
        features: {
          type: "generic",
          details: {
            General: {
              Model: "GEN-LAP-2025",
              Description: "Placeholder specs for Laptop Accessories category",
              Compatibility: "Universal for most laptops",
              Material: "Durable and lightweight",
              "Included Items": "Laptop stand, Wireless mouse, USB hub",
            },
          },
        },
        tags: [
          "Electronics",
          "Generic",
          "Laptop Accessories",
          "Utility",
          "Productivity",
        ],
      },
      {
        id: "GEN006",
        title: "Sample Product for SmartPhone",
        brand: "GenericBrand",
        category: "SmartPhone",
        comment:
          "A basic smartphone for communication and essential app usage, suitable for those on a budget.",
        vendors: {
          Amazon: {
            price: 6499,
            discountPrice: 5499,
            rating: 4.2,
            affiliateLink:
              "https://affiliate.example.com/product/GEN006/Amazon",
            offers: ["₹500 Off", "Free Shipping"],
          },
          "Tata CLiQ": {
            price: 6799,
            discountPrice: 5699,
            rating: 4.0,
            affiliateLink:
              "https://affiliate.example.com/product/GEN006/TataCLiQ",
            offers: [
              "Extra 5% off for first-time buyers",
              "Express delivery options",
            ],
          },
          JioMart: {
            price: 6699,
            discountPrice: 5599,
            rating: 4.1,
            affiliateLink:
              "https://affiliate.example.com/product/GEN006/JioMart",
            offers: ["₹200 cashback on Mobikwik", "Free Jio SIM with purchase"],
          },
        },
        image: {
          thumbnail: "https://example.com/images/generic.jpg",
          urls: ["https://example.com/images/generic.jpg"],
        },
        features: {
          type: "generic",
          details: {
            General: {
              Model: "GEN-SMA-2025",
              Description: "Placeholder specs for SmartPhone category",
              "Screen Size": "5.5 inch",
              Camera: "8MP Rear, 5MP Front",
              Battery: "3000 mAh",
              OS: "Android Go Edition",
              Storage: "32GB (expandable up to 128GB)",
              RAM: "2GB",
            },
          },
        },
        tags: [
          "Electronics",
          "Generic",
          "SmartPhone",
          "Affordable",
          "Basic Use",
        ],
      },
      {
        id: "GEN007",
        title: "Sample Product for Headphone",
        brand: "GenericBrand",
        category: "Headphone",
        comment:
          "Comfortable headphones with decent sound quality for everyday listening.",
        vendors: {
          Amazon: {
            price: 6999,
            discountPrice: 5999,
            rating: 4.0,
            affiliateLink:
              "https://affiliate.example.com/product/GEN007/Amazon",
            offers: ["₹500 Off", "Free Shipping"],
          },
          Myntra: {
            price: 7299,
            discountPrice: 6199,
            rating: 3.9,
            affiliateLink:
              "https://affiliate.example.com/product/GEN007/Myntra",
            offers: ["Seasonal discounts", "Free returns"],
          },
          Flipkart: {
            price: 7199,
            discountPrice: 6099,
            rating: 3.9,
            affiliateLink:
              "https://affiliate.example.com/product/GEN007/Flipkart",
            offers: ["SuperCoin offer", "Extended warranty"],
          },
        },
        image: {
          thumbnail: "https://example.com/images/generic.jpg",
          urls: ["https://example.com/images/generic.jpg"],
        },
        features: {
          type: "generic",
          details: {
            General: {
              Model: "GEN-HEA-2025",
              Description: "Placeholder specs for Headphone category",
              Connectivity: "Bluetooth 5.0, 3.5mm Jack",
              "Battery Life": "Up to 15 hours",
              "Noise Cancellation": "Passive Noise Isolation",
              Design: "Over-ear, Adjustable headband",
              Microphone: "Built-in microphone for calls",
            },
          },
        },
        tags: ["Electronics", "Generic", "Headphone", "Audio", "Music"],
      },
      {
        id: "GEN008",
        title: "Sample Product for Mobile Accessories",
        brand: "GenericBrand",
        category: "Mobile Accessories",
        comment:
          "Practical mobile accessories to complement your smartphone usage.",
        vendors: {
          Amazon: {
            price: 7499,
            discountPrice: 6499,
            rating: 4.2,
            affiliateLink:
              "https://affiliate.example.com/product/GEN008/Amazon",
            offers: ["₹500 Off", "Free Shipping"],
          },
          "Paytm Mall": {
            price: 7799,
            discountPrice: 6699,
            rating: 4.1,
            affiliateLink:
              "https://affiliate.example.com/product/GEN008/PaytmMall",
            offers: ["Cashback offers", "Secure payment options"],
          },
          "Reliance Digital": {
            price: 7699,
            discountPrice: 6599,
            rating: 4.0,
            affiliateLink:
              "https://affiliate.example.com/product/GEN008/RelianceDigital",
            offers: ["In-store pickup available", "Bundle deals"],
          },
        },
        image: {
          thumbnail: "https://example.com/images/generic.jpg",
          urls: ["https://example.com/images/generic.jpg"],
        },
        features: {
          type: "generic",
          details: {
            General: {
              Model: "GEN-MOB-2025",
              Description: "Placeholder specs for Mobile Accessories category",
              Compatibility: "Universal compatibility with most smartphones",
              Durability: "High-quality materials",
              Type: "Power Bank, USB Cable, Car Charger",
            },
          },
        },
        tags: [
          "Electronics",
          "Generic",
          "Mobile Accessories",
          "Convenience",
          "Utility",
        ],
      },
      {
        id: "GEN009",
        title: "Sample Product for Gaming Console",
        brand: "GenericBrand",
        category: "Gaming Console",
        comment:
          "An entry-level gaming console for casual gamers, offering basic entertainment.",
        vendors: {
          Amazon: {
            price: 7999,
            discountPrice: 6999,
            rating: 4.0,
            affiliateLink:
              "https://affiliate.example.com/product/GEN009/Amazon",
            offers: ["₹500 Off", "Free Shipping"],
          },
          "GameStop India": {
            price: 8299,
            discountPrice: 7199,
            rating: 3.9,
            affiliateLink:
              "https://affiliate.example.com/product/GEN009/GameStopIndia",
            offers: ["Bundled with a popular game", "Pre-order bonuses"],
          },
          Croma: {
            price: 8199,
            discountPrice: 7099,
            rating: 3.8,
            affiliateLink: "https://affiliate.example.com/product/GEN009/Croma",
            offers: ["Gaming accessories discounts", "Extended warranty"],
          },
        },
        image: {
          thumbnail: "https://example.com/images/generic.jpg",
          urls: ["https://example.com/images/generic.jpg"],
        },
        features: {
          type: "generic",
          details: {
            General: {
              Model: "GEN-GAM-2025",
              Description: "Placeholder specs for Gaming Console category",
              Graphics: "Standard definition output",
              Storage: "64GB internal",
              Controller: "Wireless controller included",
              Connectivity: "HDMI, USB",
            },
          },
        },
        tags: [
          "Electronics",
          "Generic",
          "Gaming Console",
          "Entertainment",
          "Casual Gaming",
        ],
      },
      {
        id: "GEN010",
        title: "Sample Product for Camera & Photo",
        brand: "GenericBrand",
        category: "Camera & Photo",
        comment: "A compact camera for capturing everyday moments with ease.",
        vendors: {
          Amazon: {
            price: 8499,
            discountPrice: 7499,
            rating: 4.2,
            affiliateLink:
              "https://affiliate.example.com/product/GEN010/Amazon",
            offers: ["₹500 Off", "Free Shipping"],
          },
          Flipkart: {
            price: 8799,
            discountPrice: 7699,
            rating: 4.1,
            affiliateLink:
              "https://affiliate.example.com/product/GEN010/Flipkart",
            offers: ["Free camera bag", "Tripod discounts"],
          },
          "Vijay Sales": {
            price: 8699,
            discountPrice: 7599,
            rating: 4.0,
            affiliateLink:
              "https://affiliate.example.com/product/GEN010/VijaySales",
            offers: ["Photography workshop voucher", "Easy EMI options"],
          },
        },
        image: {
          thumbnail: "https://example.com/images/generic.jpg",
          urls: ["https://example.com/images/generic.jpg"],
        },
        features: {
          type: "generic",
          details: {
            General: {
              Model: "GEN-CAM-2025",
              Description: "Placeholder specs for Camera & Photo category",
              Megapixels: "16MP",
              "Video Resolution": "1080p",
              Zoom: "4x Optical Zoom",
              Display: "2.7 inch LCD",
              Storage: "SD Card Slot",
              Connectivity: "USB, HDMI",
            },
          },
        },
        tags: [
          "Electronics",
          "Generic",
          "Camera & Photo",
          "Photography",
          "Compact Camera",
        ],
      },
      {
        id: "GEN011",
        title: "Sample Product for TV & Homes Appliances",
        brand: "GenericBrand",
        category: "TV & Homes Appliances",
        comment:
          "A basic home appliance for daily use, offering functionality and convenience.",
        vendors: {
          Amazon: {
            price: 8999,
            discountPrice: 7999,
            rating: 4.0,
            affiliateLink:
              "https://affiliate.example.com/product/GEN011/Amazon",
            offers: ["₹500 Off", "Free Shipping"],
          },
          Croma: {
            price: 9299,
            discountPrice: 8199,
            rating: 3.9,
            affiliateLink: "https://affiliate.example.com/product/GEN011/Croma",
            offers: [
              "Installation services available",
              "Extended warranty plans",
            ],
          },
          JioMart: {
            price: 9199,
            discountPrice: 8099,
            rating: 3.8,
            affiliateLink:
              "https://affiliate.example.com/product/GEN011/JioMart",
            offers: [
              "No-cost EMI on select credit cards",
              "Free home delivery",
            ],
          },
        },
        image: {
          thumbnail: "https://example.com/images/generic.jpg",
          urls: ["https://example.com/images/generic.jpg"],
        },
        features: {
          type: "generic",
          details: {
            General: {
              Model: "GEN-TV-2025",
              Description:
                "Placeholder specs for TV & Homes Appliances category",
              "Power Consumption": "Energy efficient",
              Dimensions: "Compact design",
              Capacity:
                "Varies by appliance type (e.g., 20L for microwave, 200L for refrigerator)",
              Functions: "Basic functions for respective appliance",
            },
          },
        },
        tags: [
          "Electronics",
          "Generic",
          "TV & Homes Appliances",
          "Home Essentials",
          "Kitchen Appliance",
        ],
      },
      {
        id: "GEN012",
        title: "Sample Product for Watches & Accessories",
        brand: "GenericBrand",
        category: "Watches & Accessories",
        comment:
          "Stylish and functional watches and accessories for everyday wear.",
        vendors: {
          Amazon: {
            price: 9499,
            discountPrice: 8499,
            rating: 4.2,
            affiliateLink:
              "https://affiliate.example.com/product/GEN012/Amazon",
            offers: ["₹500 Off", "Free Shipping"],
          },
          Myntra: {
            price: 9799,
            discountPrice: 8699,
            rating: 4.0,
            affiliateLink:
              "https://affiliate.example.com/product/GEN012/Myntra",
            offers: ["Exclusive brand discounts", "Gift wrapping options"],
          },
          Flipkart: {
            price: 9699,
            discountPrice: 8599,
            rating: 4.1,
            affiliateLink:
              "https://affiliate.example.com/product/GEN012/Flipkart",
            offers: ["SuperCoin offer", "Exchange for old watches"],
          },
        },
        image: {
          thumbnail: "https://example.com/images/generic.jpg",
          urls: ["https://example.com/images/generic.jpg"],
        },
        features: {
          type: "generic",
          details: {
            General: {
              Model: "GEN-WAT-2025",
              Description:
                "Placeholder specs for Watches & Accessories category",
              Material: "Stainless Steel, Leather, Silicone",
              "Water Resistance": "30M, 50M",
              Functions: "Time, Date, Chronograph",
              Style: "Analog, Digital, Smartwatch",
            },
          },
        },
        tags: [
          "Electronics",
          "Generic",
          "Watches & Accessories",
          "Fashion",
          "Timepiece",
        ],
      },
      {
        id: "GEN013",
        title: "Sample Product for GPS & Navigation",
        brand: "GenericBrand",
        category: "GPS & Navigation",
        comment: "A straightforward GPS device for basic navigation needs.",
        vendors: {
          Amazon: {
            price: 9999,
            discountPrice: 8999,
            rating: 4.0,
            affiliateLink:
              "https://affiliate.example.com/product/GEN013/Amazon",
            offers: ["₹500 Off", "Free Shipping"],
          },
          Flipkart: {
            price: 10299,
            discountPrice: 9199,
            rating: 3.8,
            affiliateLink:
              "https://affiliate.example.com/product/GEN013/Flipkart",
            offers: ["Map updates included", "Car mount accessory"],
          },
          "Reliance Digital": {
            price: 10199,
            discountPrice: 9099,
            rating: 3.9,
            affiliateLink:
              "https://affiliate.example.com/product/GEN013/RelianceDigital",
            offers: ["Installation support", "Extended warranty"],
          },
        },
        image: {
          thumbnail: "https://example.com/images/generic.jpg",
          urls: ["https://example.com/images/generic.jpg"],
        },
        features: {
          type: "generic",
          details: {
            General: {
              Model: "GEN-GPS-2025",
              Description: "Placeholder specs for GPS & Navigation category",
              "Screen Size": "5 inch",
              Maps: "Preloaded regional maps, Lifetime map updates",
              "Battery Life": "Up to 2 hours",
              Features:
                "Turn-by-turn directions, Speed limit display, Lane assist",
            },
          },
        },
        tags: [
          "Electronics",
          "Generic",
          "GPS & Navigation",
          "Travel",
          "Automotive",
        ],
      },
      {
        id: "GEN014",
        title: "Sample Product for Wearable Technology",
        brand: "GenericBrand",
        category: "Wearable Technology",
        comment:
          "An introductory wearable device for tracking basic fitness metrics.",
        vendors: {
          Amazon: {
            price: 10499,
            discountPrice: 9499,
            rating: 4.2,
            affiliateLink:
              "https://affiliate.example.com/product/GEN014/Amazon",
            offers: ["₹500 Off", "Free Shipping"],
          },
          "Tata CLiQ": {
            price: 10799,
            discountPrice: 9699,
            rating: 4.1,
            affiliateLink:
              "https://affiliate.example.com/product/GEN014/TataCLiQ",
            offers: [
              "Health and fitness app subscription",
              "Extended warranty",
            ],
          },
          JioMart: {
            price: 10699,
            discountPrice: 9599,
            rating: 4.0,
            affiliateLink:
              "https://affiliate.example.com/product/GEN014/JioMart",
            offers: [
              "Cashback on select payment methods",
              "Free fitness band strap",
            ],
          },
        },
        image: {
          thumbnail: "https://example.com/images/generic.jpg",
          urls: ["https://example.com/images/generic.jpg"],
        },
        features: {
          type: "generic",
          details: {
            General: {
              Model: "GEN-WAR-2025",
              Description: "Placeholder specs for Wearable Technology category",
              Display: "OLED touch display",
              Sensors: "Heart Rate, Accelerometer, Sleep Tracker",
              Connectivity: "Bluetooth 5.0",
              "Battery Life": "Up to 7 days",
              Compatibility: "Android & iOS",
              "Water Resistance": "Swim-proof",
            },
          },
        },
        tags: [
          "Electronics",
          "Generic",
          "Wearable Technology",
          "Fitness",
          "Health Tracker",
        ],
      },
    ],
  },
};
