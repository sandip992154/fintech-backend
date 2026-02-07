// Product Listing (Mobile,Laptops,products)
const a = {
  statusCode: "",
  status: "success",
  message: "Product list fetched successfully",
  data: {
    products: [
      /* array of product objects */
    ],
    pagination: {
      currentPage: 1,
      totalPages: 10,
      pageSize: 20,
      totalItems: 200,
    },
  },
};

// Filters API endpoint structure to pass to the frontend
const filters = {
  categories: [
    "All", //Default value
    "Electronics Devices",
    "Computer & Laptop",
    "Laptop Accessories",
    "SmartPhone",
    "Headphone",
    "Mobile Accessories",
    "Gaming Console",
    "Camera & Photo",
    "TV & Homes Appliances",
    "Watches & Accessories",
    "GPS & Navigation",
    "Warable Technology",
  ],
  priceRange: {
    min: 25, //default =>0
    max: 100, //default => max limit of price
  },
  priceLabels: [
    "Under Rs. 20",
    "Rs. 25 to Rs. 100",
    "Rs. 100 to Rs. 300",
    "Rs. 300 to Rs. 500",
    "Rs. 500 to Rs. 1,000",
    "Rs. 1,000 to Rs. 10,000", //default max range limit
  ],
  brands: [
    "All", //Default value
    "Apple",
    "Microsoft",
    "Dell",
    "Symphony",
    "Sony",
    "LG",
    "One Plus",
    "Google",
    "Samsung",
    "HP",
    "Xiaomi",
    "Panasonic",
  ],
  features: {
    // default values will be empty array []
    display: [
      "6.1 Inches",
      "6.2 Inches",
      "6.3 Inches",
      "6.5 Inches",
      "6.6 Inches",
    ],
    processorPerformance: [
      "Intel",
      "Silicon",
      "Apple M1",
      "Apple M2",
      "Apple M3",
      "Apple M4",
    ],
    storage: ["128 SSD", "256 SSD", "1TB SSD"],
    camera: ["50 MP", "200 MP", "200 + 200 MP", "50 + 50 MP"],
    battery: ["2580 mAh", "4000 mAh", "5000 mAh", "8000 mAh"],
  },
};
