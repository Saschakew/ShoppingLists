# 4. Database Guide

This guide provides an overview of the database schema used by the ShoppingLists application, the SQLAlchemy models that define this schema, and how database migrations are handled using Flask-Migrate.

## Database Schema Overview

The application uses a relational database to store user data, shopping lists, items within those lists, and sharing information. The primary models are `User`, `ShoppingList`, `ListItem`, and `ListShare`.

## SQLAlchemy Models (`models.py`)

The database structure is defined using SQLAlchemy ORM models located in `shopping_list_app/models.py`.

### 1. `User` Model

Represents a user in the application.

*   **Fields:**
    *   `id`: Primary key (Integer).
    *   `username`: Unique username (String).
    *   `password_hash`: Hashed password (String).
    *   `favorite_list_id`: Foreign key to `shopping_list.id`. Stores the ID of the user's designated favorite shopping list (Integer, nullable).
*   **Relationships:**
    *   `lists`: One-to-Many with `ShoppingList` (via `ShoppingList.owner_id`). Represents all lists owned by this user.
    *   `items_added`: One-to-Many with `ListItem` (via `ListItem.added_by_id`). Represents all items added by this user across all lists.
    *   `favorite_list`: Many-to-One with `ShoppingList`. Provides direct access to the user's favorite list object.
    *   `shared_lists` (backref from `ListShare.user`): Represents all `ListShare` entries associated with this user, effectively listing which lists are shared *with* them.
*   **Methods:**
    *   `set_password(password)`: Hashes the given password and stores it.
    *   `check_password(password)`: Verifies a given password against the stored hash.

### 2. `ShoppingList` Model

Represents a single shopping list.

*   **Fields:**
    *   `id`: Primary key (Integer).
    *   `name`: Name of the shopping list (String).
    *   `owner_id`: Foreign key to `user.id`. The ID of the user who owns this list (Integer).
    *   `created_at`: Timestamp of when the list was created (DateTime, defaults to `datetime.utcnow`).
*   **Relationships:**
    *   `owner` (backref from `User.lists`): Provides access to the `User` object who owns this list.
    *   `items`: One-to-Many with `ListItem`. All items belonging to this list. `cascade="all, delete-orphan"` ensures that if a list is deleted, all its associated items are also deleted.
    *   `shares`: One-to-Many with `ListShare`. All sharing records for this list. `cascade="all, delete-orphan"` ensures that if a list is deleted, all its sharing records are also deleted.

### 3. `ListItem` Model

Represents an individual item within a shopping list.

*   **Fields:**
    *   `id`: Primary key (Integer).
    *   `list_id`: Foreign key to `shopping_list.id`. The ID of the list this item belongs to (Integer).
    *   `item_name`: Name of the item (String).
    *   `category`: Category of the item (String, nullable, defaults to 'Other').
    *   `is_purchased`: Boolean flag indicating if the item has been purchased (Boolean, defaults to `False`).
    *   `added_by_id`: Foreign key to `user.id`. The ID of the user who added this item (Integer).
    *   `added_at`: Timestamp of when the item was added (DateTime, defaults to `datetime.utcnow`).
*   **Relationships:**
    *   `list` (backref from `ShoppingList.items`): Provides access to the `ShoppingList` object this item belongs to.
    *   `adder` (backref from `User.items_added`): Provides access to the `User` object who added this item.

### 4. `ListShare` Model

An association table that manages the many-to-many relationship for sharing shopping lists between users.

*   **Fields:**
    *   `id`: Primary key (Integer).
    *   `list_id`: Foreign key to `shopping_list.id`. The ID of the list being shared (Integer).
    *   `user_id`: Foreign key to `user.id`. The ID of the user with whom the list is shared (Integer).
*   **Relationships:**
    *   `list` (backref from `ShoppingList.shares`): Provides access to the `ShoppingList` object that is shared.
    *   `user` (backref to `User.shared_lists`): Provides access to the `User` object with whom the list is shared.
*   **Constraints:**
    *   `__table_args__ = (db.UniqueConstraint('list_id', 'user_id', name='_list_user_uc'),)`: Ensures that a specific list can only be shared with a specific user once, preventing duplicate sharing entries.

## Database Migrations (Flask-Migrate)

The application uses Flask-Migrate (which uses Alembic under the hood) to manage changes to the database schema over time. This is crucial for evolving the application without losing existing data.

### Workflow

1.  **Initialization (One-time setup per environment):**
    If you're setting up the migrations system for the first time in a new environment (or if the `migrations` directory doesn't exist):
    ```bash
    flask db init
    ```
    This creates a `migrations` directory and a configuration file.

2.  **Generating a New Migration:**
    Whenever you make changes to your SQLAlchemy models in `models.py` (e.g., add a new table, add a column to an existing table, change a column type), you need to generate a new migration script:
    ```bash
    flask db migrate -m "Descriptive message about the changes"
    ```
    For example: `flask db migrate -m "Add category to ListItem model"`.
    This command inspects your models, compares them to the current state of the database (as tracked by previous migrations), and generates a new script in the `migrations/versions/` directory.
    **Important:** Always review the generated migration script to ensure it accurately reflects the intended changes. Sometimes Alembic might not detect certain changes perfectly (e.g., table name changes, complex constraint changes) and might require manual adjustments to the script.

3.  **Applying Migrations:**
    To apply the generated migration (and any pending migrations) to your database, run:
    ```bash
    flask db upgrade
    ```
    This will execute the `upgrade()` function in the migration script(s), altering the database schema.

4.  **Downgrading Migrations (Reverting):**
    If you need to revert the last applied migration, you can use:
    ```bash
    flask db downgrade
    ```
    You can also downgrade to a specific migration version.

### Important Considerations:

*   **Development vs. Production:**
    *   In development, you frequently run `migrate` and `upgrade`.
    *   In production, you typically only run `flask db upgrade` during deployment to apply new, tested migrations. Generating migrations (`flask db migrate`) should be done in a development environment.
*   **Version Control:** The `migrations/` directory (especially `migrations/versions/`) should be committed to your version control system (Git). This ensures that all developers and deployment environments have the same migration history.
*   **SQLite Limitations:** While SQLite is convenient for development, it has limitations regarding schema alterations (e.g., dropping columns, altering constraints can be tricky). Alembic tries to work around these, but complex migrations are more robustly handled by databases like PostgreSQL or MySQL, which are recommended for production.
*   **Initial Database Creation:**
    *   For a brand new setup where the database doesn't exist yet, running `flask db upgrade` will create all tables based on the full migration history.
    *   The `db.create_all()` method (often found in `app.py` or `application.py` for initial quick starts) can also create tables based on current models, but it bypasses the migration history. For projects using Flask-Migrate, it's generally recommended to rely on `flask db upgrade` to establish the schema, even for the first time.

By following this migration workflow, developers can collaboratively and safely evolve the database schema as the application grows.
