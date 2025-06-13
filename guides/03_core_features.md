# 3. Core Features

This guide details the main functionalities of the ShoppingLists application, covering user accounts, list and item management, sharing, and real-time collaboration.

## 1. User Account Management (`auth.py`)

The application provides robust user authentication and account management features:

*   **User Registration (`/register`):**
    *   New users can create an account by providing a username and password.
    *   Passwords are securely hashed before being stored in the database.
    *   Checks for existing usernames to ensure uniqueness.

*   **User Login (`/login`):**
    *   Registered users can log in using their username and password.
    *   The application supports persistent login sessions ("Remember Me") for up to one year.

*   **User Logout (`/logout`):**
    *   Allows authenticated users to securely log out of their accounts.

*   **Access Control:**
    *   Many features and routes are protected using the `@login_required` decorator from Flask-Login, ensuring only authenticated users can access them.

## 2. Dashboard (`main.py` - `/dashboard`)

Upon logging in, users are typically directed to their dashboard, which serves as a central hub:

*   **List Overview:** Displays all shopping lists that the user either owns or that have been shared with them.
*   **Create New List:** Provides a simple form to create a new shopping list by specifying its name.

## 3. Shopping List Management (`main.py`)

Users have comprehensive control over their shopping lists:

*   **List Creation:**
    *   From the dashboard, users can quickly create new lists.
    *   Each new list is associated with the logged-in user as its owner.

*   **List Viewing (`/list/<int:list_id>`):
    *   Displays the details of a specific shopping list, including all its items.
    *   Shows item attributes like name, category, who added it, and when it was added.
    *   Features real-time updates for item additions, deletions, and status changes (purchased/not purchased) using SocketIO.

*   **List Deletion (`/list/<int:list_id>/delete`):
    *   Only the owner of a shopping list can delete it.
    *   A confirmation mechanism is in place to prevent accidental deletions (as implemented per `MEMORY[050e754f-72d8-42df-be52-4330035d8c2d]` via a modal in `share_list.html`).
    *   If a user deletes a list that was marked as their favorite, the favorite status is automatically cleared.

*   **List Sharing:**
    *   **Sharing Management Page (`/list/<int:list_id>/share`):** Provides a user interface for list owners to manage who their list is shared with.
    *   **Sharing Action (POST to `/list/<int:list_id>/share`):** Owners can share their lists with other registered users by entering their username. They can also revoke sharing access.

*   **Set as Favorite List (`/list/<int:list_id>/set_favorite`):
    *   Users can designate one of their accessible lists as a "favorite."
    *   If a favorite list is set, the application's home page (`/`) will automatically redirect to this list for quick access.

## 4. Item Management (`main.py`)

Within each list, users can manage individual shopping items:

*   **Adding Items:**
    *   Can be done through a traditional form submission on the list detail page.
    *   Also supported via a JavaScript-driven API endpoint (`/api/list/<int:list_id>/add_item`) for a smoother, non-page-reloading experience.
    *   Each item includes a name, an optional category (defaults to "Other"), and tracks which user added it.
    *   A `item_added` SocketIO event is broadcast to all users viewing the list for real-time updates.

*   **Deleting Items:**
    *   Initially handled by a route (`/delete_item/<int:item_id>`).
    *   Enhanced with an API endpoint (`/api/list/<int:list_id>/delete_item`) for client-side deletion.
    *   **Permissions (as per `MEMORY[1405b01f-c27c-4c5f-9977-baa709b6894f]`):** An item can be deleted by the list owner OR any user with whom the list is shared.
    *   A `item_deleted` SocketIO event is broadcast for real-time updates.

*   **Marking Items as Purchased:**
    *   Users can toggle the purchased status of items within a list (e.g., by clicking a checkbox or button).
    *   This action triggers an `item_status_changed` SocketIO event, ensuring all collaborators see the updated status in real-time.

## 5. Real-Time Collaboration (SocketIO)

The application leverages Flask-SocketIO to provide a collaborative experience:

*   **Dedicated Rooms:** Each shopping list operates within its own SocketIO room (e.g., `list_123`). This ensures that updates are only sent to clients currently viewing that specific list.
*   **Events:**
    *   `item_added`: Sent when a new item is added to a list.
    *   `item_deleted`: Sent when an item is removed from a list.
    *   `item_status_changed`: Sent when an item's purchased status is toggled.
    *   *(Potentially other events like `list_updated` for changes to list properties, though not explicitly detailed in current outlines.)*

## 6. API Endpoints for Enhanced UX (`main.py`)

To support dynamic frontend interactions without full page reloads, several API endpoints are available:

*   **`POST /api/list/<int:list_id>/add_item`:** Adds a new item to the specified list.
*   **`POST /api/list/<int:list_id>/delete_item`:** Deletes an item from the specified list.
*   **`GET /api/list/<int:list_id>/updates_since?timestamp=<float>`:** Allows clients to fetch all changes (items added, deleted, status changed) to a list since a given Unix timestamp. This can be used for polling or to reconcile client-side state if a SocketIO connection was temporarily lost.
