# Phase 3: Public API Endpoints Implementation Plan

## Overview
Implement the public API endpoints for the Pangan Indonesia Data API, starting with `GET /prices` as the core functionality. This phase builds upon the completed ingestion pipeline (Phase 2) and follows the existing Clean Architecture patterns.

## Current Architecture Context
- **Clean Architecture**: API → Use Cases → Ports → Infrastructure
- **Existing Patterns**: Health endpoints follow router delegation, Pydantic schemas, functional ports
- **Database**: SQLAlchemy with relationships, existing PriceRepositoryPort with basic query support
- **Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2.0

## Technical Requirements (from RFC)
- **Endpoint**: `GET /prices`
- **Required Query Param**: `level_harga_id` (int)
- **Optional Query Params**: `commodity_id`, `province_id`, `period_start`, `period_end`, `limit`, `offset`
- **Response**: Price records with commodity/province names, price, unit, period, level
- **Sorting**: Default `period_start DESC`
- **Pagination**: Limit/offset with total count

## Implementation Plan

### Phase 3.1: API Schemas & Models (Week 1)

#### ✅ Task 3.1.1: Define Query Parameters Schema (COMPLETED)
- ✅ Create `PriceQueryParams` Pydantic model in `app/api/schemas.py`
- ✅ Include all query parameters with proper validation:
  - ✅ `level_harga_id: int` (required)
  - ✅ `commodity_id: str | None`
  - ✅ `province_id: str | None`
  - ✅ `period_start: date | None` (YYYY-MM-DD format)
  - ✅ `period_end: date | None` (YYYY-MM-DD format)
  - ✅ `limit: int = 50` (max 1000, min 1)
  - ✅ `offset: int = 0` (min 0)
- ✅ Add field validators for date format and range validation

#### ✅ Task 3.1.2: Define Response Schemas (COMPLETED)
- ✅ Create `PriceResponse` model with all required fields:
  - ✅ `id: int`
  - ✅ `commodity_id: str`
  - ✅ `commodity_name: str`
  - ✅ `province_id: str`
  - ✅ `province_name: str`
  - ✅ `level_harga_id: int`
  - ✅ `period_start: date`
  - ✅ `period_end: date`
  - ✅ `price: float`
  - ✅ `unit: str`
- ✅ Create `PaginatedPriceResponse` wrapper:
  - ✅ `data: List[PriceResponse]`
  - ✅ `total: int`
  - ✅ `limit: int`
  - ✅ `offset: int`

#### ✅ Task 3.1.3: Update Ports (COMPLETED)
- ✅ Review existing `PriceQuery` and `PriceRecord` in `ports.py`
- ✅ Add `commodity_name` and `province_name` fields to `PriceRecord`
- ✅ Create new `PaginatedPriceResult` DTO for structured API responses
- ✅ Update `QueryPricesFn` callable to return `PaginatedPriceResult` instead of tuple
- ✅ Update `prices.py` repository to perform joins and return structured results

**Success Criteria**:
- All Pydantic models validate correctly
- Field validation works for edge cases
- OpenAPI schema generation is clean

### Phase 3.2: Database Query Enhancement (Week 1-2)

#### ✅ Task 3.2.1: Enhance Price Repository (COMPLETED)
- ✅ Update `prices.py` repository to support joins with commodities and provinces
- ✅ Implement `_to_record()` function to map joined results (renamed from `_to_record_with_names()`)
- ✅ Modify `query()` method to:
  - ✅ Join with `commodities` and `provinces` tables using `joinedload()`
  - ✅ Select required fields: commodity_name, province_name
  - ✅ Maintain existing filtering and pagination logic
  - ✅ Ensure proper type conversion (Decimal → float for API)

#### ✅ Task 3.2.2: Optimize Query Performance (COMPLETED)
- ✅ Add database indexes if needed for query performance (created migration)
- ✅ Implement proper SQL joins to avoid N+1 queries (using joinedload)
- ✅ Add query execution time logging (detailed timing and metrics)
- Test query performance with realistic data volumes (ready for testing)

#### ✅ Task 3.2.3: Error Handling in Repository (COMPLETED)
- ✅ Add proper error handling for database connection issues
- ✅ Implement timeout handling for long-running queries (via SQLAlchemy)
- ✅ Add logging for query execution details (comprehensive error logging)
- ✅ Add batch processing error resilience (continue on individual failures)

**Success Criteria**:
- Query returns correct data with joined commodity/province names
- Performance meets <150ms target for typical queries
- Proper error handling and logging

### Phase 3.3: Use Case Layer Implementation (Week 2)

#### ✅ Task 3.3.1: Create Price Query Use Case (COMPLETED)
- ✅ Create `app/usecases/price_service.py` (functional approach)
- ✅ Implement `query_prices()` function following RORO pattern
- ✅ Add input validation at use case level with comprehensive checks
- ✅ Implement business logic validation (date ranges, level_harga_id, pagination)

#### ✅ Task 3.3.2: Add Business Logic Validation (COMPLETED)
- ✅ Validate date ranges (period_start <= period_end, reasonable date bounds)
- ✅ Validate level_harga_id is within expected range (1-5)
- ✅ Validate pagination parameters (limit 1-1000, offset >= 0)
- ✅ Validate string parameters are not empty
- ✅ Optional entity existence validation (commodities/provinces)

#### ✅ Task 3.3.3: Add Comprehensive Error Handling (COMPLETED)
- ✅ Handle repository layer errors gracefully with proper exception wrapping
- ✅ Implement proper error types (ValueError for validation, RuntimeError for system errors)
- ✅ Add structured logging for use case operations with detailed context
- ✅ Graceful handling of optional repository failures (commodity/province validation)

**Success Criteria**:
- Use case handles all valid inputs correctly
- Proper error responses for invalid inputs
- Comprehensive logging for debugging

### Phase 3.4: API Endpoint Implementation (Week 2-3)

#### Task 3.4.1: Create Prices Router
- Create `app/api/prices.py` following existing patterns
- Implement `GET /prices` endpoint with:
  - Query parameter extraction and validation
  - Delegation to use case layer
  - Proper response formatting
  - OpenAPI documentation and examples

#### Task 3.4.2: Add Input Validation & Error Handling
- Implement 400/422 responses for invalid inputs
- Add custom error responses for business logic violations
- Ensure proper HTTP status codes throughout

#### Task 3.4.3: Add API Metadata & Documentation
- Add comprehensive OpenAPI descriptions
- Include request/response examples
- Add endpoint tags and summaries
- Configure response models for proper schema generation

**Success Criteria**:
- Endpoint returns 200 with correct JSON for valid requests
- Proper 400/422 responses for invalid inputs
- OpenAPI docs are comprehensive and accurate

### Phase 3.5: Integration & Testing (Week 3-4)

#### Task 3.5.1: Update Main Router
- Add prices router to main API router in `app/api/router.py`
- Ensure proper prefix and tags configuration
- Test router integration

#### Task 3.5.2: Comprehensive Testing
- Write unit tests for use case functions
- Write integration tests with database
- Test pagination edge cases (offset, limit bounds)
- Test filtering combinations
- Performance test with realistic data volumes

#### Task 3.5.3: Documentation & Examples
- Create curl examples for common use cases
- Document API usage patterns
- Add performance characteristics documentation

**Success Criteria**:
- All tests pass including edge cases
- Performance meets <150ms target
- Comprehensive documentation available

## Dependencies & Prerequisites

### Required Before Starting Phase 3
- ✅ Phase 1: Database & Models (completed)
- ✅ Phase 2: Ingestion & Idempotent Upsert (completed)
- ✅ Database populated with test data
- ✅ Existing repository patterns established

### External Dependencies
- FastAPI + Pydantic v2 (already in requirements.txt)
- SQLAlchemy 2.0 (already installed)
- PostgreSQL with populated data

## Risk Mitigation

### Technical Risks
1. **Query Performance**: Implement proper indexing and monitor query execution times
2. **Memory Usage**: Use pagination limits to prevent large result sets
3. **Type Conversion**: Careful handling of Decimal → float conversion for API responses
4. **Concurrent Access**: Repository methods should handle concurrent database access

### Business Logic Risks
1. **Data Consistency**: Ensure joined data remains consistent
2. **Date Range Validation**: Proper validation of period_start/end parameters
3. **Level Harga Validation**: Validate against known level_harga_id values

## Success Criteria for Phase 3

### Functional Requirements
- [ ] `GET /prices?level_harga_id=3` returns 200 with paginated price data
- [ ] Filtering works correctly for all parameters
- [ ] Pagination returns correct total counts and subsets
- [ ] Response includes commodity_name and province_name fields
- [ ] Sorting defaults to period_start DESC

### Performance Requirements
- [ ] Response time < 150ms for typical queries (50-100 records)
- [ ] Proper database query optimization (joins, indexes)
- [ ] Memory usage remains bounded for large result sets

### Quality Requirements
- [ ] Comprehensive input validation with clear error messages
- [ ] Proper HTTP status codes (200, 400, 422, 500)
- [ ] OpenAPI documentation is complete and accurate
- [ ] No SQL injection vulnerabilities
- [ ] Proper error handling and logging

### Testing Requirements
- [ ] Unit tests for all use case functions
- [ ] Integration tests with database
- [ ] Edge case testing for pagination and filtering
- [ ] Performance testing with realistic data volumes

## Timeline & Milestones

### Week 1: Foundation
- Complete API schemas and models
- Enhance repository with joins
- Basic use case implementation

### Week 2: Core Implementation
- Complete use case with validation
- Implement API endpoint
- Basic testing and integration

### Week 3: Refinement
- Comprehensive testing
- Performance optimization
- Documentation completion

### Week 4: Validation
- End-to-end testing
- Performance validation
- Documentation review

## Next Phase Preparation
Once Phase 3 is complete, Phase 4 (Scheduling & Reliability) can begin with:
- APScheduler integration in FastAPI lifespan
- Weekly refresh and monthly rebuild jobs
- OS cron redundancy setup

## Open Questions
1. Should we implement caching at the API level for frequently accessed data?
2. Do we need rate limiting from day one?
3. Should we add data freshness indicators to responses?
4. Do we need to support additional sort options beyond period_start DESC?
