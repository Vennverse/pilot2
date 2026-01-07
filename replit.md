# FlowPilot - AI Automation Platform

## Overview

FlowPilot is an AI-powered automation platform that allows users to create and execute workflow automations using natural language. Users describe what they want to automate in plain English, the system generates an execution plan using AI, and users can review, approve, and run these automations. The platform connects to various third-party services (like Gmail, Slack) to perform actions on the user's behalf.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: React 18 with TypeScript, built using Vite
- **Styling**: Tailwind CSS with CSS variables for theming (dark mode default)
- **UI Components**: shadcn/ui component library built on Radix UI primitives
- **State Management**: TanStack React Query for server state, React hooks for local state
- **Routing**: React Router v6 with client-side navigation
- **Animations**: Framer Motion for page transitions and micro-interactions

### Backend Architecture
- **API Server**: Python Flask application with CORS enabled
- **AI Integration**: OpenAI API (via Replit AI Integrations) for natural language processing
- **Endpoint Pattern**: RESTful API with `/api/` prefix
- **Key Endpoints**:
  - `/api/health` - Health check
  - `/api/ai-planner` - Generates execution plans from natural language prompts

### Authentication & Authorization
- **Provider**: Supabase Auth for user authentication
- **Flow**: Email/password authentication with session management
- **Protected Routes**: Dashboard and Settings require authenticated users
- **Session Handling**: Client-side auth state via Supabase JS client

### Data Storage
- **Backend**: Supabase (PostgreSQL) for persistent storage
- **Data Models**:
  - Providers (third-party service definitions with actions)
  - Credentials (encrypted OAuth tokens and API keys per user/provider)
  - Execution Plans (user-created automation workflows)

### Provider Integration System
- **Auth Types**: OAuth 2.0 and API key authentication
- **Credential Storage**: Encrypted tokens stored in Supabase
- **Action Catalog**: Each provider has defined actions with parameters (e.g., Gmail send_email, Slack post_message)

## External Dependencies

### Third-Party Services
- **Supabase**: Authentication, PostgreSQL database, and real-time subscriptions
- **OpenAI API**: AI-powered plan generation from natural language (accessed via Replit AI Integrations)

### Key npm Packages
- `@supabase/supabase-js` - Supabase client
- `@tanstack/react-query` - Data fetching and caching
- `react-router-dom` - Client-side routing
- `framer-motion` - Animations
- `zod` - Schema validation
- `lucide-react` - Icon library
- Radix UI primitives - Accessible UI components

### Python Packages
- `flask` - Web framework
- `flask-cors` - CORS handling
- `openai` - OpenAI API client