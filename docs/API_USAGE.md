# Pangan Indonesia Data API - Usage Guide

## Overview

The Pangan Indonesia Data API provides access to Indonesian food price data with comprehensive filtering, pagination, and high performance. This guide covers common usage patterns, examples, and best practices.

## Base URL

```
https://your-api-domain.com
```

## Authentication

Currently, no authentication is required for the public API endpoints.

## Core Endpoint: `/prices`

The main endpoint for querying price data with full filtering and pagination support.

### Required Parameters

- `level_harga_id` (integer): Price level identifier (1-5)
  - 1: Producer level
  - 2: Wholesale level
  - 3: Consumer level (most common)
  - 4: Retail level
  - 5: Export level

### Optional Parameters

- `commodity_id` (string): Filter by specific commodity ID
- `province_id` (string): Filter by specific province ID
- `period_start` (date): Filter prices from this date (YYYY-MM-DD)
- `period_end` (date): Filter prices until this date (YYYY-MM-DD)
- `limit` (integer): Number of records per page (1-1000, default: 50)
- `offset` (integer): Number of records to skip (default: 0)

### Response Format

```json
{
  "data": [
    {
      "id": 1,
      "commodity_id": "01",
      "commodity_name": "Beras",
      "province_id": "NATIONAL",
      "province_name": "National Aggregate",
      "level_harga_id": 3,
      "period_start": "2024-11-01",
      "period_end": "2024-11-30",
      "price": 9500.0,
      "unit": "Rp./Kg"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

## Common Usage Examples

### 1. Get Latest Consumer Prices

Get the most recent consumer-level prices (default sorting is by period_start descending).

```bash
curl "https://api.example.com/prices?level_harga_id=3"
```

### 2. Get Prices for Specific Commodity

Get all prices for rice (commodity_id: "01") at consumer level.

```bash
curl "https://api.example.com/prices?level_harga_id=3&commodity_id=01"
```

### 3. Get Prices for Specific Time Period

Get consumer prices for November 2024.

```bash
curl "https://api.example.com/prices?level_harga_id=3&period_start=2024-11-01&period_end=2024-11-30"
```

### 4. Get Prices for Specific Commodity and Time Period

Get rice prices for November 2024.

```bash
curl "https://api.example.com/prices?level_harga_id=3&commodity_id=01&period_start=2024-11-01&period_end=2024-11-30"
```

### 5. Pagination

Get first 10 records:

```bash
curl "https://api.example.com/prices?level_harga_id=3&limit=10&offset=0"
```

Get next 10 records:

```bash
curl "https://api.example.com/prices?level_harga_id=3&limit=10&offset=10"
```

### 6. Advanced Filtering

Get wholesale prices for corn in East Java province for Q1 2024:

```bash
curl "https://api.example.com/prices?level_harga_id=2&commodity_id=02&province_id=35&period_start=2024-01-01&period_end=2024-03-31"
```

## Error Handling

### HTTP Status Codes

- `200`: Success
- `400`: Bad Request (validation errors)
- `422`: Unprocessable Entity (parameter validation)
- `500`: Internal Server Error

### Error Response Format

```json
{
  "detail": "Error message describing the issue"
}
```

### Common Error Examples

Invalid level_harga_id:
```bash
curl "https://api.example.com/prices?level_harga_id=10"
# Returns: 422 Unprocessable Content
```

Invalid date range:
```bash
curl "https://api.example.com/prices?level_harga_id=3&period_end=2024-01-01&period_start=2024-12-31"
# Returns: 400 Bad Request - "period_end must be after or equal to period_start"
```

## Performance Characteristics

### Response Times

- **Target**: < 150ms for typical queries
- **Basic queries**: 20-50ms
- **Filtered queries**: 15-40ms
- **Complex queries**: 30-80ms

### Pagination Performance

- Page size doesn't significantly impact response time
- Large offsets are handled efficiently
- Memory usage remains bounded

### Database Optimization

- Uses indexed queries for fast filtering
- Efficient JOIN operations for commodity/province names
- Connection pooling for high concurrency

## Best Practices

### 1. Use Appropriate Page Sizes

- Default limit (50) is good for most use cases
- Use smaller limits (10-25) for mobile applications
- Use larger limits (100-500) for data analysis

### 2. Implement Efficient Pagination

- Start with offset=0, then increment by your page size
- Monitor the `total` field to know when you've reached the end
- Consider cursor-based pagination for very large datasets

### 3. Handle Rate Limiting

- Implement client-side caching for frequently accessed data
- Use appropriate delays between requests
- Monitor API response headers for rate limit information

### 4. Data Processing

- Parse dates correctly (YYYY-MM-DD format)
- Handle decimal prices appropriately
- Validate commodity and province IDs from `/commodities` and `/provinces` endpoints

### 5. Error Handling

- Always check HTTP status codes
- Implement exponential backoff for retries
- Log errors for debugging

## Data Freshness

- Data is updated weekly (every Monday)
- Monthly rebuild ensures historical data accuracy
- Check the `inserted_at` field for record timestamps

## Data Coverage

- **Commodities**: 20+ food commodities
- **Provinces**: National aggregate and individual provinces
- **Time Range**: 2020 to present
- **Price Levels**: All 5 levels (1-5)
- **Update Frequency**: Weekly updates

## SDKs and Libraries

### Python Example

```python
import requests
from typing import List, Dict, Any

class PanganAPI:
    def __init__(self, base_url: str = "https://api.example.com"):
        self.base_url = base_url

    def get_prices(self, **params) -> Dict[str, Any]:
        """Get prices with filtering and pagination."""
        response = requests.get(f"{self.base_url}/prices", params=params)
        response.raise_for_status()
        return response.json()

    def get_all_prices_paginated(self, **filters) -> List[Dict[str, Any]]:
        """Get all prices using pagination."""
        all_data = []
        offset = 0
        limit = 1000

        while True:
            params = {**filters, "limit": limit, "offset": offset}
            result = self.get_prices(**params)
            all_data.extend(result["data"])

            if len(result["data"]) < limit:
                break
            offset += limit

        return all_data

# Usage
api = PanganAPI()
prices = api.get_prices(level_harga_id=3, commodity_id="01", limit=50)
print(f"Found {prices['total']} price records")
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

class PanganAPI {
  constructor(baseURL = 'https://api.example.com') {
    this.client = axios.create({ baseURL });
  }

  async getPrices(params) {
    const response = await this.client.get('/prices', { params });
    return response.data;
  }

  async getAllPricesPaginated(filters) {
    const allData = [];
    let offset = 0;
    const limit = 1000;

    while (true) {
      const params = { ...filters, limit, offset };
      const result = await this.getPrices(params);
      allData.push(...result.data);

      if (result.data.length < limit) break;
      offset += limit;
    }

    return allData;
  }
}

// Usage
const api = new PanganAPI();
const prices = await api.getPrices({
  level_harga_id: 3,
  commodity_id: '01',
  limit: 50
});
console.log(`Found ${prices.total} price records`);
```

## Monitoring and Support

### Health Checks

Check API availability:
```bash
curl "https://api.example.com/health/healthz"
```

Check database connectivity:
```bash
curl "https://api.example.com/health/readyz"
```

### OpenAPI Documentation

Interactive API documentation:
```
https://api.example.com/docs
```

OpenAPI JSON specification:
```
https://api.example.com/openapi.json
```

## Changelog

### Version 0.1.0
- Initial release with `/prices` endpoint
- Basic filtering and pagination
- Consumer, wholesale, and producer price levels
- National aggregate data
