# Database Schema Documentation

## Overview
The Task Manager application uses PostgreSQL as its primary database with SQLAlchemy ORM for Python integration.

## Database Models

### 1. Users Table
Stores user authentication and profile information.
- **id** (UUID): Primary key
- **username** (String): Unique username
- **email** (String): Unique email address
- **password_hash** (String): Bcrypt hashed password
- **full_name** (String): User's full name
- **avatar_url** (String): Profile picture URL
- **last_login** (DateTime): Last login timestamp
- **is_active** (Boolean): Account active status

### 2. Projects Table
Manages project information and organization.
- **id** (UUID): Primary key
- **name** (String): Project name
- **description** (Text): Project description
- **owner_id** (UUID): Foreign key to Users
- **color** (String): Hex color for UI theming
- **icon** (String): Project icon identifier
- **is_archived** (Boolean): Archive status

### 3. Tasks Table
Core task management entity.
- **id** (UUID): Primary key
- **title** (String): Task title
- **description** (Text): Task details
- **project_id** (UUID): Foreign key to Projects
- **assignee_id** (UUID): Foreign key to Users (nullable)
- **creator_id** (UUID): Foreign key to Users
- **status** (Enum): todo, in_progress, review, done
- **priority** (Enum): low, medium, high, urgent
- **due_date** (DateTime): Task deadline
- **estimated_hours** (Float): Time estimate
- **actual_hours** (Float): Actual time spent
- **completed_at** (DateTime): Completion timestamp

### 4. Comments Table
Task discussion and collaboration.
- **id** (UUID): Primary key
- **task_id** (UUID): Foreign key to Tasks
- **user_id** (UUID): Foreign key to Users
- **content** (Text): Comment text
- **is_edited** (Boolean): Edit status

### 5. Tags Table
Categorization system for tasks.
- **id** (UUID): Primary key
- **name** (String): Tag name
- **color** (String): Hex color code
- **project_id** (UUID): Foreign key to Projects (nullable for global tags)

### 6. Junction Tables

#### TaskTags
Many-to-many relationship between tasks and tags.
- **task_id** (UUID): Foreign key to Tasks
- **tag_id** (UUID): Foreign key to Tags

#### ProjectMembers
Many-to-many relationship with roles.
- **project_id** (UUID): Foreign key to Projects
- **user_id** (UUID): Foreign key to Users
- **role** (Enum): viewer, member, admin
- **joined_at** (DateTime): Membership date

### 7. ActivityLogs Table
Audit trail and activity tracking.
- **id** (UUID): Primary key
- **user_id** (UUID): Foreign key to Users
- **project_id** (UUID): Foreign key to Projects
- **task_id** (UUID): Foreign key to Tasks (nullable)
- **action** (Enum): Action type
- **details** (JSONB): Additional context
- **created_at** (DateTime): Activity timestamp

## Database Setup

### Prerequisites
- PostgreSQL 14 or higher
- Python 3.11 or higher

### Installation Steps

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create database:**
   ```sql
   CREATE DATABASE task_manager_dev;
   ```

3. **Set environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Run migrations:**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

## Indexes
- Users: username, email (unique)
- ActivityLogs: created_at
- Junction tables have composite primary keys

## Performance Considerations
- UUID primary keys for better distribution
- JSONB for flexible activity log details
- Proper indexes on frequently queried columns
- Connection pooling configured in SQLAlchemy