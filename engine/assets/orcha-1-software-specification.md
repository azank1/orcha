# Orcha-1 Software Specification Document

**Project**: Orcha-1  
**Version**: 0.0.1  
**Date**: September 21, 2025  
**Author**: azank1  
**License**: MIT  

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Architecture Design](#architecture-design)
4. [Component Specifications](#component-specifications)
5. [API Documentation](#api-documentation)
6. [Data Models](#data-models)
7. [Technology Stack](#technology-stack)
8. [Deployment Guide](#deployment-guide)
9. [Security Considerations](#security-considerations)
10. [Performance Requirements](#performance-requirements)
11. [Testing Strategy](#testing-strategy)
12. [Maintenance & Support](#maintenance--support)

---

## Executive Summary

### Project Overview
Orcha-1 is a sophisticated food ordering orchestration system that provides a standardized interface for restaurant automation workflows. The system implements a multi-layer architecture consisting of a Model Context Protocol (MCP) server and a Policy Proxy layer, designed to integrate with n8n automation workflows and the FoodTec PizzaBolis restaurant management system.

### Business Value
- **Automation**: Enables automated food ordering workflows through n8n
- **Standardization**: Provides consistent API interface via Model Context Protocol
- **Reliability**: Implements idempotency and error handling for order processing
- **Performance**: Includes intelligent caching strategies for menu data
- **Integration**: Seamless connection between automation tools and restaurant APIs

### Key Features
- JSON-RPC 2.0 compliant MCP server
- Intelligent menu caching with configurable TTL
- Idempotent order processing
- Comprehensive error handling and validation
- Mock implementation for development and testing

---

## System Overview

### Purpose Statement
Orcha-1 serves as an orchestration layer that enables automated food ordering workflows by providing a standardized interface between n8n automation platform and FoodTec restaurant APIs.

### System Context
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   n8n Platform  │───▶│   MCP Server    │───▶│  Policy Proxy   │───▶│  FoodTec API    │
│   (Automation)  │    │  (JSON-RPC)     │    │  (Caching/Rules)│    │  (Restaurant)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Capabilities
1. **Menu Management**: Export and cache restaurant menus by store
2. **Order Validation**: Validate order drafts against available inventory
3. **Order Processing**: Accept and process orders with duplicate prevention
4. **Error Handling**: Comprehensive error management and reporting
5. **Tool Discovery**: Expose available operations via MCP protocol

---

## Architecture Design

### System Architecture

#### High-Level Architecture
The system follows a layered architecture pattern with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Layer (n8n)                      │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                   Protocol Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   MCP Server    │  │   JSON-RPC      │                  │
│  │   (Port 9090)   │  │   Endpoint      │                  │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                   Business Logic Layer                     │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  Policy Proxy   │  │     Caching     │                  │
│  │  (Port 8080)    │  │     Strategy    │                  │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                   Integration Layer                        │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  FoodTec API    │  │   HTTP Client   │                  │
│  │   (External)    │  │   (node-fetch)  │                  │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

#### Component Interaction
1. **n8n** sends JSON-RPC requests to MCP Server
2. **MCP Server** validates requests and forwards to Policy Proxy
3. **Policy Proxy** applies business rules, caching, and calls upstream APIs
4. **Response** flows back through layers with appropriate error handling

### Design Patterns

#### 1. Proxy Pattern
- MCP Server acts as a proxy between client and business logic
- Policy Proxy acts as a proxy between business logic and external APIs
- Enables clean separation of concerns and protocol translation

#### 2. Cache-Aside Pattern
- Menu data cached with TTL-based invalidation
- Reduces upstream API calls and improves response times
- Configurable cache duration for different deployment scenarios

#### 3. Idempotency Pattern
- Order processing uses idempotency keys to prevent duplicates
- UUID-based key generation with manual override capability
- Maintains order ledger for replay protection

#### 4. Error Boundary Pattern
- Structured error handling at each layer
- Consistent error response format across all endpoints
- Proper HTTP status codes and error categorization

---

## Component Specifications

### MCP Server Component

#### Overview
The MCP Server implements the Model Context Protocol specification, providing a JSON-RPC 2.0 interface for tool discovery and execution.

#### Technical Specifications
- **Framework**: Express.js
- **Port**: 9090 (configurable via `MCP_PORT`)
- **Protocol**: JSON-RPC 2.0 over HTTP
- **Module System**: ES2022 modules
- **Request Limit**: 1MB JSON payload

#### Exposed Tools

##### 1. foodtec.export_menu
**Purpose**: Export menu data for a specific store
**Parameters**:
```typescript
{
  type: "object",
  properties: {
    store_id: { type: "string" }
  }
}
```
**Behavior**:
- Forwards request to Policy Proxy `/menu` endpoint
- Handles store_id parameter as query parameter
- Returns cached menu data with store-specific content

##### 2. foodtec.validate_order
**Purpose**: Validate order draft before submission
**Parameters**:
```typescript
{
  type: "object"
  // Flexible schema for order validation
}
```
**Behavior**:
- Forwards order draft to Policy Proxy `/validateOrder` endpoint
- Returns validation results with errors/warnings
- Provides pricing and substitution information

##### 3. foodtec.accept_order
**Purpose**: Accept and process validated orders
**Parameters**:
```typescript
{
  type: "object",
  properties: {
    draft: { type: "object" },
    idem: { type: "string" }
  }
}
```
**Behavior**:
- Generates or uses provided idempotency key
- Forwards to Policy Proxy `/acceptOrder` endpoint
- Returns order confirmation with tracking information

#### Error Handling
The MCP Server implements comprehensive error handling following JSON-RPC 2.0 specifications:

**Error Codes**:
- `-32600`: Invalid Request (malformed JSON-RPC)
- `-32601`: Method Not Found (unknown tool)
- `-32000`: Upstream Error (policy proxy failures)
- `-32098`: Proxy Failure (network/connectivity issues)

#### Health Check
- **Endpoint**: `GET /healthz`
- **Response**: System status including proxy connectivity
- **Usage**: Monitoring and deployment verification

### Policy Proxy Component

#### Overview
The Policy Proxy implements business logic, caching strategies, and upstream API integration for the food ordering system.

#### Technical Specifications
- **Framework**: Express.js
- **Port**: 8080 (configurable via `PORT`)
- **Cache**: In-memory with TTL (10 minutes default)
- **Module System**: ES2022 modules
- **Development**: Hot reload with nodemon

#### Caching Strategy

##### Menu Caching
- **TTL**: 600,000ms (10 minutes) configurable
- **Key Format**: `menu:{store_id}`
- **Behavior**: Cache-aside pattern with automatic expiration
- **Storage**: In-memory Map structure

##### Cache Benefits
- Reduced upstream API calls
- Improved response times
- Cost optimization for external API usage
- Resilience during upstream service degradation

#### API Endpoints

##### GET /apiclient/menu
**Purpose**: Export menu data with intelligent caching
**Query Parameters**:
- `store_id` (optional): Specific store identifier

**Response Format**:
```json
{
  "ok": true,
  "store_id": "default",
  "categories": [
    {
      "id": "pizzas",
      "name": "Pizzas", 
      "items": [
        {
          "sku": "LARGE_PEP",
          "name": "Large Pepperoni",
          "price": 14.99
        }
      ]
    }
  ]
}
```

##### POST /apiclient/validateOrder
**Purpose**: Validate order drafts against business rules
**Request Body**: Order draft object
**Validation Rules**:
- Required `items` array with valid SKUs
- SKU validation against allowlist
- Business rule enforcement

**Success Response**:
```json
{
  "ok": true,
  "totals": {
    "amount": 18.75,
    "currency": "USD"
  },
  "warnings": [],
  "substitutions": []
}
```

**Error Response** (422):
```json
{
  "ok": false,
  "code": "VALIDATION",
  "message": "Unknown SKU(s): INVALID_SKU",
  "meta": { "status": 422 }
}
```

##### POST /apiclient/acceptOrder
**Purpose**: Process validated orders with idempotency
**Headers**:
- `Idempotency-Key` (optional): UUID for duplicate prevention

**Request Body**: Validated order object
**Idempotency Behavior**:
- Generates UUID if not provided
- Maintains order ledger for replay protection
- Returns same response for duplicate requests

**Response**:
```json
{
  "ok": true,
  "order_id": "PB-1695312000000",
  "eta_minutes": 25,
  "received_at": "2025-09-21T10:00:00.000Z"
}
```

#### Business Logic

##### Order Validation
1. **Structure Validation**: Ensures required fields are present
2. **SKU Validation**: Checks against approved product catalog
3. **Business Rules**: Applies store-specific restrictions
4. **Pricing Calculation**: Computes totals and applicable taxes

##### Idempotency Management
1. **Key Generation**: UUID v4 for unique identification
2. **Ledger Storage**: In-memory storage for processed orders
3. **Replay Detection**: Returns cached response for duplicates
4. **Header Propagation**: Returns idempotency key in response

---

## API Documentation

### Model Context Protocol Interface

#### Tool Discovery
**Endpoint**: `GET /.well-known/mcp/tools`
**Purpose**: Discover available tools and their specifications
**Response**: Array of tool definitions with parameters

#### JSON-RPC Endpoint
**Endpoint**: `POST /rpc`
**Content-Type**: `application/json`
**Protocol**: JSON-RPC 2.0

#### Request Format
```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "method": "tool.method.name",
  "params": {
    "parameter1": "value1",
    "parameter2": "value2"
  }
}
```

#### Response Format
**Success**:
```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "result": {
    "data": "response-data"
  }
}
```

**Error**:
```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "error": {
    "code": -32000,
    "message": "Error description",
    "data": "additional-error-info"
  }
}
```

### REST API Interface

#### Base URL
- Development: `http://localhost:8080/apiclient`
- Production: Configurable via environment variables

#### Authentication
Currently implements mock authentication. Production deployment should include:
- API key authentication
- Rate limiting
- Request signing validation

#### Content Types
- Request: `application/json`
- Response: `application/json`
- Character Encoding: UTF-8

---

## Data Models

### Menu Model
```typescript
interface MenuResponse {
  ok: boolean;
  store_id: string;
  categories: Category[];
}

interface Category {
  id: string;
  name: string;
  items: MenuItem[];
}

interface MenuItem {
  sku: string;
  name: string;
  price: number;
}
```

### Order Models
```typescript
interface OrderDraft {
  items: OrderItem[];
  customer?: CustomerInfo;
  delivery?: DeliveryInfo;
}

interface OrderItem {
  sku: string;
  quantity: number;
  modifications?: string[];
}

interface ValidationResponse {
  ok: boolean;
  totals: {
    amount: number;
    currency: string;
  };
  warnings: string[];
  substitutions: Substitution[];
}

interface OrderConfirmation {
  ok: boolean;
  order_id: string;
  eta_minutes: number;
  received_at: string;
}
```

### Error Models
```typescript
interface ApiError {
  ok: false;
  code: string;
  message: string;
  meta: {
    status: number;
  };
}

interface JsonRpcError {
  jsonrpc: "2.0";
  id: string | number | null;
  error: {
    code: number;
    message: string;
    data?: any;
  };
}
```

---

## Technology Stack

### Runtime Environment
- **Node.js**: ^20.x (LTS recommended)
- **Module System**: ES2022 modules
- **Package Manager**: npm

### Core Dependencies

#### Production Dependencies
- **express**: ^4.18.2 - Web application framework
- **node-fetch**: ^3.3.2 - HTTP client for upstream API calls
- **uuid**: ^9.0.1 - UUID generation for idempotency

#### Development Dependencies
- **typescript**: ^5.5.4 - TypeScript compiler
- **@types/express**: ^4.17.21 - Express TypeScript definitions
- **@types/node**: ^20.11.30 - Node.js TypeScript definitions
- **@types/uuid**: ^10.0.0 - UUID TypeScript definitions
- **nodemon**: ^3.0.2 - Development file watching (proxy only)

### Build Tools
- **TypeScript Compiler**: ES2022 target with strict mode
- **Module Resolution**: Node.js style resolution
- **Output**: CommonJS compatible with ES modules

### Development Tools
- **Hot Reload**: nodemon for development workflow
- **Type Checking**: Strict TypeScript configuration
- **Code Organization**: Modular package structure

---

## Deployment Guide

### Prerequisites
- Node.js 20.x or higher
- npm package manager
- Git for source control

### Installation Steps

#### 1. Clone Repository
```bash
git clone https://github.com/azank1/orcha-1.git
cd orcha-1
```

#### 2. Install Dependencies
```bash
# Install root dependencies
npm install

# Install MCP Server dependencies
cd mcp_server
npm install

# Install Proxy dependencies
cd ../proxy
npm install
```

#### 3. Build Applications
```bash
# Build MCP Server
cd mcp_server
npm run build

# Build Proxy
cd ../proxy
npm run build
```

### Configuration

#### Environment Variables

##### MCP Server Configuration
```bash
MCP_PORT=9090                    # MCP server port
PROXY_BASE=http://127.0.0.1:8080/apiclient  # Proxy base URL
```

##### Proxy Configuration
```bash
PORT=8080                        # Proxy server port
FOODTEC_BASE=https://pizzabolis-lab.foodtecsolutions.com/apiclient
FOODTEC_MENU_KEY=...            # API key for menu endpoints
FOODTEC_VALIDATE_KEY=...        # API key for validation endpoints
FOODTEC_ACCEPT_KEY=...          # API key for order acceptance
CACHE_TTL_SEC=600               # Cache TTL in seconds
RETRY_MAX=2                     # Maximum retry attempts
```

### Production Deployment

#### 1. Process Management
Use PM2 or similar process manager:
```bash
# Start MCP Server
pm2 start mcp_server/dist/index.js --name mcp-server

# Start Proxy
pm2 start proxy/dist/index.js --name policy-proxy
```

#### 2. Reverse Proxy
Configure nginx or similar:
```nginx
# MCP Server
location /mcp/ {
    proxy_pass http://localhost:9090/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

# Policy Proxy
location /apiclient/ {
    proxy_pass http://localhost:8080/apiclient/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

#### 3. Health Monitoring
Both services provide health check endpoints:
- MCP Server: `GET http://localhost:9090/healthz`
- Policy Proxy: `GET http://localhost:8080/healthz`

### Development Workflow

#### 1. Development Mode
```bash
# Start Proxy in watch mode
cd proxy
npm run dev

# Start MCP Server in watch mode
cd ../mcp_server
npm run dev
```

#### 2. Testing
```bash
# Test MCP Server health
curl http://localhost:9090/healthz

# Test tool discovery
curl http://localhost:9090/.well-known/mcp/tools

# Test menu export
curl "http://localhost:8080/apiclient/menu?store_id=test"
```

---

## Security Considerations

### Current Security Posture
The current implementation is designed for development and testing environments with basic security measures.

### Security Features Implemented
1. **Request Size Limiting**: 1MB JSON payload limit
2. **Input Validation**: Basic parameter validation
3. **Error Handling**: Structured error responses without sensitive data exposure

### Security Recommendations for Production

#### 1. Authentication & Authorization
- Implement API key authentication for all endpoints
- Add role-based access control for different operations
- Use JWT tokens for session management

#### 2. Network Security
- Deploy behind HTTPS with valid SSL certificates
- Implement rate limiting to prevent abuse
- Use Web Application Firewall (WAF) for additional protection

#### 3. Data Protection
- Sanitize all input parameters
- Implement request/response logging with PII redaction
- Use environment variables for sensitive configuration

#### 4. API Security
- Implement request signing for upstream API calls
- Add timeout configuration for external API calls
- Use circuit breaker pattern for upstream service failures

#### 5. Monitoring & Alerting
- Log security events and suspicious activities
- Monitor for unusual traffic patterns
- Implement alerting for service degradation

### Compliance Considerations
- **PCI DSS**: Required for payment processing
- **GDPR**: For customer data handling
- **SOC 2**: For service organization controls

---

## Performance Requirements

### Service Level Objectives (SLOs)

#### Availability
- **Target**: 99.9% uptime
- **Measurement**: Monthly availability percentage
- **Acceptable Downtime**: 43.2 minutes per month

#### Response Time
- **Menu Export**: < 200ms (95th percentile)
- **Order Validation**: < 500ms (95th percentile)
- **Order Acceptance**: < 1000ms (95th percentile)

#### Throughput
- **Concurrent Requests**: 100 requests/second
- **Menu Cache Hit Rate**: > 95%
- **Order Processing Rate**: 50 orders/minute

### Performance Optimizations

#### Caching Strategy
- **Menu Caching**: 10-minute TTL reduces upstream calls by 95%
- **Response Compression**: gzip compression for large payloads
- **Keep-Alive Connections**: Persistent connections to upstream APIs

#### Resource Management
- **Memory Usage**: < 512MB per service instance
- **CPU Usage**: < 50% during normal operations
- **Connection Pooling**: Reuse HTTP connections for efficiency

#### Scalability Patterns
- **Horizontal Scaling**: Stateless services support load balancing
- **Database Scaling**: In-memory cache can be replaced with Redis
- **CDN Integration**: Static menu content can be cached at edge locations

### Monitoring Metrics

#### Application Metrics
- Request rate and response times
- Error rates by endpoint and error type
- Cache hit/miss ratios
- Upstream API response times

#### Infrastructure Metrics
- CPU and memory utilization
- Network I/O and disk usage
- Process health and restart counts
- Load balancer metrics

---

## Testing Strategy

### Testing Pyramid

#### Unit Tests
**Scope**: Individual functions and components
**Tools**: Jest, TypeScript
**Coverage Target**: 90% code coverage

**Test Categories**:
- JSON-RPC request/response handling
- Cache management logic
- Error handling scenarios
- Data validation functions

#### Integration Tests
**Scope**: Component interaction and API contracts
**Tools**: Supertest, Jest
**Coverage**: All API endpoints

**Test Scenarios**:
- MCP Server to Policy Proxy communication
- Error propagation between layers
- Idempotency key handling
- Cache behavior verification

#### End-to-End Tests
**Scope**: Complete workflow validation
**Tools**: Newman, Postman collections
**Coverage**: Critical user journeys

**Test Flows**:
- Complete order workflow (menu → validate → accept)
- Error handling scenarios
- Cache invalidation behavior
- Idempotency verification

### Test Data Management

#### Mock Data
- Standardized menu data for consistent testing
- Various order scenarios (valid, invalid, edge cases)
- Error response templates

#### Test Environments
- **Local**: Developer workstation with mocked upstream
- **Staging**: Replica environment with test data
- **Production**: Live environment with real integrations

### Automated Testing

#### Continuous Integration
```yaml
# Example GitHub Actions workflow
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
      - run: npm ci
      - run: npm test
      - run: npm run build
```

#### Performance Testing
- Load testing with artillery.js or k6
- Stress testing for failure scenarios
- Cache performance validation

---

## Maintenance & Support

### Operational Procedures

#### Deployment Process
1. **Code Review**: Peer review for all changes
2. **Testing**: Automated test suite execution
3. **Staging**: Deploy to staging environment
4. **Validation**: End-to-end testing in staging
5. **Production**: Blue-green deployment strategy
6. **Monitoring**: Post-deployment verification

#### Backup & Recovery
- **Configuration Backup**: Environment variables and settings
- **Log Retention**: 30-day log retention policy
- **Disaster Recovery**: Service restart procedures

#### Monitoring & Alerting
- **Health Checks**: Automated service monitoring
- **Performance Alerts**: Response time and error rate thresholds
- **Capacity Planning**: Resource utilization tracking

### Support Procedures

#### Incident Response
1. **Detection**: Automated monitoring alerts
2. **Triage**: Severity assessment and assignment
3. **Investigation**: Log analysis and debugging
4. **Resolution**: Fix implementation and testing
5. **Post-Mortem**: Root cause analysis and prevention

#### Maintenance Windows
- **Scheduled**: Monthly maintenance windows
- **Emergency**: Critical security patches
- **Upgrades**: Quarterly dependency updates

### Documentation Maintenance

#### Technical Documentation
- **API Documentation**: OpenAPI specification updates
- **Architecture Diagrams**: System design documentation
- **Runbooks**: Operational procedures and troubleshooting

#### Knowledge Base
- **Common Issues**: FAQ and troubleshooting guides
- **Configuration**: Environment setup instructions
- **Integration**: Third-party service documentation

---

## Appendices

### Appendix A: Configuration Reference

#### Complete Environment Variables
```bash
# MCP Server
MCP_PORT=9090
PROXY_BASE=http://127.0.0.1:8080/apiclient

# Policy Proxy  
PORT=8080
FOODTEC_BASE=https://pizzabolis-lab.foodtecsolutions.com/apiclient
FOODTEC_MENU_KEY=your-menu-api-key
FOODTEC_VALIDATE_KEY=your-validation-api-key  
FOODTEC_ACCEPT_KEY=your-acceptance-api-key
CACHE_TTL_SEC=600
RETRY_MAX=2

# Optional
NODE_ENV=production
LOG_LEVEL=info
```

### Appendix B: Error Code Reference

#### JSON-RPC Error Codes
- `-32700`: Parse error (Invalid JSON)
- `-32600`: Invalid Request (Missing required fields)
- `-32601`: Method not found (Unknown tool)
- `-32602`: Invalid params (Parameter validation failed)
- `-32603`: Internal error (Unexpected server error)
- `-32000`: Upstream error (Policy proxy failures)
- `-32098`: Proxy failure (Network connectivity issues)

#### HTTP Status Codes
- `200`: Success
- `400`: Bad Request (Invalid input)
- `422`: Unprocessable Entity (Validation failed)
- `500`: Internal Server Error
- `502`: Bad Gateway (Upstream failure)
- `503`: Service Unavailable (Maintenance mode)

### Appendix C: Integration Examples

#### n8n Workflow Integration
```json
{
  "nodes": [
    {
      "name": "Get Menu",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://localhost:9090/rpc",
        "method": "POST",
        "body": {
          "jsonrpc": "2.0",
          "id": "1",
          "method": "foodtec.export_menu",
          "params": {"store_id": "main"}
        }
      }
    }
  ]
}
```

#### cURL Examples
```bash
# Tool Discovery
curl -X GET http://localhost:9090/.well-known/mcp/tools

# Menu Export
curl -X POST http://localhost:9090/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1", 
    "method": "foodtec.export_menu",
    "params": {"store_id": "test"}
  }'

# Order Validation
curl -X POST http://localhost:9090/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "2",
    "method": "foodtec.validate_order", 
    "params": {
      "items": [{"sku": "LARGE_PEP", "quantity": 1}]
    }
  }'
```

---

**Document Version**: 1.0  
**Last Updated**: September 21, 2025  
**Next Review**: December 21, 2025  

*This document represents the complete software specification for the Orcha-1 food ordering orchestration system. For updates and additional documentation, please refer to the project repository.*