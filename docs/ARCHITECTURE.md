# Cert Me Boi - System Architecture

## Overview

Cert Me Boi is designed as a modular, extensible system for automated course certification. The architecture follows clean code principles and emphasizes maintainability, testability, and reliability.

## Core Components

### 1. Logger System (`src/utils/logger.py`)
- Multi-handler logging with rotation
- Structured logging with context
- Separate error and general logs
- Automatic log cleanup
- Debug mode support

### 2. Screen Monitor (`src/monitor/screen_monitor.py`) 
- Real-time screen capture using MSS
- OpenCV-based image analysis
- Template matching
- Region-based monitoring
- Video progress tracking

### 3. Browser Automation (`src/automation/browser.py`)
- Playwright-based browser control
- Stealth mode operation
- Multi-browser support
- Robust element selection
- Error recovery

### 4. AI Model Handler (`src/ai/model_handler.py`)
- Local model support
- OpenRouter API integration
- Text generation
- Image analysis
- OCR capabilities

### 5. Main Application (`src/main.py`)
- Component orchestration
- Error handling
- State management
- Course progression tracking

## Data Flow

1. User initiates automation with course credentials
2. Main application orchestrates components:
   - Browser launches and logs in
   - Screen monitor starts tracking
   - AI assists with content interpretation
   - Logger records all actions

3. For each course section:
   - Screen monitor detects content type
   - Browser performs necessary actions
   - AI assists with quizzes/assignments
   - Logger maintains audit trail

## Error Handling

1. Browser Errors
   - Automatic retry with backoff
   - Session recovery
   - Screenshot capture
   - Error logging

2. AI Model Errors
   - Fallback to simpler models
   - Request retry logic
   - Error reporting

3. Screen Monitor Errors
   - Frame capture retry
   - Alternative region analysis
   - Error notification

## Configuration

1. Course Platforms (`config/courses.yaml`)
   - Platform-specific selectors
   - Authentication settings
   - Navigation patterns

2. AI Models (`config/courses.yaml`)
   - Model selection
   - API configurations
   - Performance settings

3. Monitoring (`config/courses.yaml`)
   - Screen regions
   - Update intervals
   - Template configurations

## Security

1. Credential Management
   - Environment variables
   - Secure storage
   - Session management

2. API Security
   - Key rotation
   - Rate limiting
   - Request validation

## Extensibility

1. New Platforms
   - Platform adapter interface
   - Selector configuration
   - Authentication handler

2. Additional AI Models
   - Model wrapper interface
   - API integration
   - Response parsing

3. Custom Monitoring
   - Monitor plugin system
   - Custom analyzers
   - Event handlers

## Testing

1. Unit Tests
   - Component isolation
   - Mock integrations
   - Error scenarios

2. Integration Tests
   - Component interaction
   - End-to-end flows
   - Performance metrics

3. System Tests
   - Full system validation
   - Load testing
   - Recovery testing 