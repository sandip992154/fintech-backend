import pytest
import asyncio
from httpx import AsyncClient
from app import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_get_latest_popular(client):
    """Test latest popular products endpoint"""
    response = await client.get("/products/latest-popular")
    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert isinstance(data["products"], list)

@pytest.mark.asyncio
async def test_get_hot_deals(client):
    """Test hot deals endpoint"""
    response = await client.get("/products/hot-deals")
    assert response.status_code == 200
    data = response.json()
    assert "products" in data

@pytest.mark.asyncio
async def test_search_products(client):
    """Test product search endpoint"""
    response = await client.get("/products/search?query=phone")
    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert "pagination" in data

@pytest.mark.asyncio
async def test_get_categories(client):
    """Test categories endpoint"""
    response = await client.get("/categories")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert isinstance(data["categories"], list)

@pytest.mark.asyncio
async def test_get_brands(client):
    """Test brands endpoint"""
    response = await client.get("/brands")
    assert response.status_code == 200
    data = response.json()
    assert "brands" in data

@pytest.mark.asyncio
async def test_compare_products(client):
    """Test product comparison endpoint"""
    # This would need valid product IDs
    response = await client.post(
        "/products/compare",
        json=["test_id_1", "test_id_2"]
    )
    # Might return 404 if products don't exist, which is expected
    assert response.status_code in [200, 404]

@pytest.mark.asyncio
async def test_contact_us(client):
    """Test contact form endpoint"""
    contact_data = {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "1234567890",
        "message": "This is a test message"
    }
    response = await client.post("/contact-us", json=contact_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

@pytest.mark.asyncio
async def test_ping(client):
    """Test health check endpoint"""
    response = await client.get("/ping")
    assert response.status_code == 200
    data = response.json()
    assert data["res"] is True

@pytest.mark.asyncio
async def test_product_detail_not_found(client):
    """Test product detail with invalid ID"""
    response = await client.get("/product/invalid_id")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_search_with_filters(client):
    """Test search with various filters"""
    params = {
        "query": "laptop",
        "category": "computer",
        "min_price": 30000,
        "max_price": 100000,
        "sort_by": "1",
        "page": 1,
        "limit": 10
    }
    response = await client.get("/products/search", params=params)
    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert "pagination" in data

if __name__ == "__main__":
    pytest.main(["-v", __file__])