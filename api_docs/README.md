# PFA Counseling API Documentation and Client

This directory contains the API documentation and a sample client application for the PFA Counseling Application.

## Contents

1. [API Documentation](index.html) - Comprehensive documentation of all API endpoints, authentication, and examples.
2. [Sample Client Application](client/index.html) - A React-based web client that demonstrates API usage.

## Getting Started

1. Start the PFA Counseling Application main server
2. The API will be available at `http://localhost:8000/api/v1`
3. Open the API documentation or Sample Client in your browser

## Authentication

To use the API, you need to authenticate first:

```
POST /api/v1/auth/login

{
    "username": "admin",
    "password": "admin"
}
```

This will return a JWT token that you need to include in the Authorization header for all other requests:

```
Authorization: Bearer <token>
```