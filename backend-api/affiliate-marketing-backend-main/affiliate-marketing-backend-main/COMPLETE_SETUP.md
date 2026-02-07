# 🛒 Affiliate Marketing Platform - Complete Setup Guide

A full-stack affiliate marketing platform with React frontend and FastAPI backend featuring multi-platform product scraping and price comparison.

## 🏗️ Architecture

**Frontend:** React 19.1.0 + Vite + Tailwind CSS  
**Backend:** FastAPI + Python with web scraping  
**Database:** MongoDB Atlas  
**Scraping:** Selenium + BeautifulSoup for Amazon, Flipkart, Croma, JioMart, Vijay Sales  

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- Python 3.9+
- MongoDB Atlas account

### Backend Setup

1. **Navigate to backend directory:**
```bash
cd affiliate-marketing-backend-main/affiliate-marketing-backend-main
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**
Create `.env` file:
```env
# Database Configuration
MONGO_URL=your_mongodb_connection_string
DB_NAME=ecommerce_db

# Email Configuration (optional)
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password
EMAIL_RECEIVER=admin@yoursite.com
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
```

4. **Run data synchronization (first time):**
```bash
python sync_data.py
```

5. **Start the API server:**
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd affiliate-marketing-main
```

2. **Install Node dependencies:**
```bash
npm install
```

3. **Configure environment variables:**
Update `.env` file:
```env
VITE_URL=http://localhost:8000
```

4. **Start development server:**
```bash
npm run dev
```

### Access the Application
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## 🛠️ Key Features Implemented

### ✅ Backend API Endpoints

#### Products
- `GET /products/latest-popular` - Get trending products
- `GET /products/hot-deals` - Get discounted products  
- `GET /products/best-selling` - Get top-rated products
- `GET /product/{id}` - Get individual product details
- `GET /products/search` - Search products with filters
- `POST /products/compare` - Compare multiple products

#### Categories & Filters
- `GET /categories` - Get all product categories
- `GET /brands` - Get available brands (with optional category filter)

#### Contact
- `POST /contact-us` - Submit contact form with email notifications

### ✅ Frontend Pages & Components

#### Pages
- **Home** - Product showcases with API integration
- **Products** - Searchable product listing with filters
- **Product Details** - Individual product pages
- **Category** - Category-based product browsing
- **Compare** - Product comparison tool
- **Contact Us** - Contact form with validation

#### Components
- **Responsive Design** - Mobile-first approach
- **Product Cards** - Unified product display
- **Search & Filters** - Advanced filtering system
- **Pagination** - Efficient product browsing
- **Loading States** - User-friendly loading indicators
- **Error Handling** - Graceful error management

### ✅ Web Scraping System

#### Supported Platforms
- Amazon India
- Flipkart  
- Croma
- JioMart
- Vijay Sales

#### Product Categories
- Mobiles/Smartphones
- Laptops/Computers
- Mobile Accessories
- Laptop Accessories

#### Scraper Features
- **Parallel Processing** - Multiple scrapers run concurrently
- **Data Standardization** - Unified product schema
- **Price Comparison** - Cross-platform price tracking
- **Error Handling** - Robust scraping with fallbacks

---

## 🗂️ Data Schema

### Unified Product Format
```json
{
  "id": "unique_product_id",
  "title": "Product Title",
  "brand": "Brand Name", 
  "category": "SmartPhone",
  "image": "image_url",
  "description": "Product description",
  "features": ["feature1", "feature2"],
  "tags": ["tag1", "tag2"],
  "vendors": {
    "amazon": {
      "price": 25000,
      "discountprice": 23000,
      "rating": 4.5,
      "reviews": 1200,
      "availability": "In Stock",
      "link": "product_url",
      "offers": {}
    }
    // ... other vendors
  },
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

---

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
# Required
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/db
DB_NAME=ecommerce_db

# Optional Email Setup
EMAIL_USER=notifications@yoursite.com
EMAIL_PASS=app_password
EMAIL_RECEIVER=admin@yoursite.com

# Scraping Configuration
SCRAPER_DELAY=2
SCRAPER_MAX_PAGES=5
SCRAPER_CONCURRENT_LIMIT=3
```

#### Frontend (.env)
```env
# API Base URL
VITE_URL=https://your-backend-url.com
# or for local development
VITE_URL=http://localhost:8000
```

---

## 📊 API Usage Examples

### Search Products
```javascript
// Search with filters
const response = await fetch('/products/search?query=iphone&category=smartphone&min_price=20000&max_price=80000&sort_by=-1&page=1&limit=20');
```

### Get Product Details
```javascript
// Get specific product
const response = await fetch('/product/12345abc');
```

### Compare Products
```javascript
// Compare multiple products
const response = await fetch('/products/compare', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify(['product_id_1', 'product_id_2', 'product_id_3'])
});
```

---

## 🏃‍♂️ Running Scrapers

### Manual Scraper Execution
```bash
# Run all scrapers
python run_all_scrappers.py

# Run data synchronization
python sync_data.py
```

### Scraper Output Structure
```
core/database/
├── mobiles/
│   ├── amazon.json
│   ├── flipkart.json
│   ├── croma.json
│   └── _combined.json
├── laptop/
├── mobileaccessories/
└── laptopaccessories/
```

---

## 🚀 Deployment

### Backend (Render/Railway)
1. Connect your repository
2. Set environment variables
3. Install command: `pip install -r requirements.txt`
4. Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`

### Frontend (Netlify/Vercel)
1. Connect your repository
2. Set build command: `npm run build`
3. Set publish directory: `dist`
4. Set environment variable: `VITE_URL=your_backend_url`

### Database Setup
1. Create MongoDB Atlas cluster
2. Create database user
3. Get connection string
4. Update MONGO_URL in backend .env

---

## 🔍 Troubleshooting

### Common Issues

**API Connection Errors**
- Check VITE_URL in frontend .env
- Ensure backend is running on correct port
- Verify CORS settings in FastAPI

**Database Connection Issues** 
- Verify MongoDB connection string
- Check database user permissions
- Ensure network access is allowed

**Scraper Failures**
- Check internet connection
- Verify website availability
- Update CSS selectors if sites have changed

**Build Errors**
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node.js version compatibility
- Verify all dependencies are installed

---

## 📚 Project Structure

```
affiliate-marketing-main/          # Frontend React App
├── src/
│   ├── components/               # Reusable components
│   ├── pages/                   # Route components  
│   ├── services/                # API services
│   └── assets/                  # Static assets
├── public/                      # Public assets
└── package.json

affiliate-marketing-backend-main/  # Backend FastAPI App
├── services/                    # API route handlers
├── utils/                      # Database utilities
├── core/                       # Web scraping modules
│   ├── mobiles/               # Mobile scrapers
│   ├── laptop/               # Laptop scrapers
│   └── database/             # Scraped data storage
├── app.py                     # Main FastAPI app
├── sync_data.py              # Data standardization
└── requirements.txt
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Email: support@yoursite.com
- Documentation: Check API docs at `/docs` endpoint

---

## 🙏 Acknowledgments

- React team for the excellent frontend framework
- FastAPI for the high-performance Python web framework
- MongoDB for the flexible database solution
- All the e-commerce platforms for providing product data

---

*Happy coding! 🚀*