from flask import url_for
from shopping_list_app.app import ShoppingList, ListItem, ListShare, User

# Helper function to get a user (could be a fixture too)
def get_user(db_session, username):
    return db_session.query(User).filter_by(username=username).first()

def test_index_page(client):
    """Test that the index page loads."""
    response = client.get(url_for('main.index'))
    assert response.status_code == 200
    assert b'Welcome to the Family Shopping List App' in response.data

def test_dashboard_unauthenticated(client):
    """Test dashboard access when not logged in (should redirect to login)."""
    response = client.get(url_for('main.dashboard'), follow_redirects=True)
    assert response.status_code == 200
    assert url_for('auth.login') in response.request.path
    # Check for login required message
    assert b'login' in response.data.lower()

def test_dashboard_authenticated(auth_client_fixture):
    """Test dashboard access when logged in."""
    authed_client = auth_client_fixture(username='dashuser')
    response = authed_client.get(url_for('main.dashboard'))
    assert response.status_code == 200
    # Check for dashboard content - just verify we have the dashboard page
    assert b'dashboard' in response.data.lower()

def test_create_shopping_list(auth_client_fixture, app, db):
    """Test creating a new shopping list."""
    authed_client = auth_client_fixture(username='listowner')
    list_name = 'Groceries for the Week'
    response = authed_client.post(url_for('main.dashboard'), data={'list_name': list_name}, follow_redirects=True)
    assert response.status_code == 200
    # Check for list creation success message
    assert b'created' in response.data.lower()
    assert list_name.encode() in response.data # Check if list name appears on dashboard

    with app.app_context():
        user = get_user(db.session, 'listowner')
        assert user is not None
        shopping_list = db.session.query(ShoppingList).filter_by(name=list_name, owner_id=user.id).first()
        assert shopping_list is not None
        assert shopping_list.owner == user

def test_view_list_detail_and_add_item(auth_client_fixture, app, db):
    """Test viewing a list's detail page and adding an item."""
    authed_client = auth_client_fixture(username='itemadder')
    user_id = None
    with app.app_context(): # Get user within app context
        user = get_user(db.session, 'itemadder')
        assert user is not None
        user_id = user.id  # Store the user ID to avoid DetachedInstanceError
        # Create a list for this user directly
        new_list = ShoppingList(name='My Test List', owner_id=user_id)
        db.session.add(new_list)
        db.session.commit()
        list_id = new_list.id

    # View list detail page
    response = authed_client.get(url_for('main.list_detail', list_id=list_id))
    assert response.status_code == 200
    assert b'My Test List' in response.data

    # Add an item
    item_name = 'Milk'
    response = authed_client.post(url_for('main.list_detail', list_id=list_id), data={'item_name': item_name}, follow_redirects=True)
    assert response.status_code == 200
    # Check for item addition success message
    assert b'added to' in response.data and b'Milk' in response.data
    assert item_name.encode() in response.data

    with app.app_context():
        list_item = db.session.query(ListItem).filter_by(item_name=item_name, list_id=list_id).first()
        assert list_item is not None
        assert list_item.added_by_id == user_id

def test_delete_item_from_list(auth_client_fixture, app, db):
    """Test deleting an item from a list."""
    authed_client = auth_client_fixture(username='itemdeleter')
    user = None
    item_id_to_delete = None
    list_id_for_item = None

    with app.app_context():
        user = get_user(db.session, 'itemdeleter')
        assert user is not None
        # Create list and item
        shopping_list = ShoppingList(name='List With Item', owner_id=user.id)
        db.session.add(shopping_list)
        db.session.commit()
        list_id_for_item = shopping_list.id

        list_item = ListItem(item_name='Bread to Delete', list_id=list_id_for_item, added_by_id=user.id)
        db.session.add(list_item)
        db.session.commit()
        item_id_to_delete = list_item.id
    
    # Delete the item
    response = authed_client.post(url_for('main.delete_item', item_id=item_id_to_delete), follow_redirects=True)
    assert response.status_code == 200
    # Check for item deletion success message
    assert b'deleted from' in response.data
    # Verify item is no longer on the page
    # We need to check the actual content area, not the flash message
    assert b'<li id="item-' not in response.data

    with app.app_context():
        deleted_item = db.session.query(ListItem).get(item_id_to_delete)
        assert deleted_item is None

def test_share_list(auth_client_fixture, create_user_fixture, app, db):
    """Test sharing a list with another user."""
    owner_client = auth_client_fixture(username='listownerforshare')
    owner_user = None
    shared_user = None
    list_id_to_share = None

    with app.app_context():
        owner_user = get_user(db.session, 'listownerforshare')
        assert owner_user is not None
        # Create another user to share with
        shared_user = create_user_fixture(username='sharedwithuser', password='password')
        assert shared_user is not None

        # Owner creates a list
        shopping_list = ShoppingList(name='Shared List Test', owner_id=owner_user.id)
        db.session.add(shopping_list)
        db.session.commit()
        list_id_to_share = shopping_list.id

    # Owner shares the list
    response = owner_client.post(url_for('main.share_list', list_id=list_id_to_share), 
                                 data={'share_with_username': 'sharedwithuser'}, 
                                 follow_redirects=True)
    assert response.status_code == 200
    # Check for the presence of the shared username in the response
    assert b'sharedwithuser' in response.data
    # Check for the success message (allowing for HTML encoding of quotes)
    assert b'List' in response.data and b'Shared List Test' in response.data and b'shared with sharedwithuser' in response.data
    assert b'sharedwithuser' in response.data # Check if shared user appears on page

    # Store the username as a string (not an object attribute)
    shared_username = 'sharedwithuser'
    
    with app.app_context():
        # Get the shared user by username
        shared_user_from_db = db.session.query(User).filter_by(username=shared_username).first()
        assert shared_user_from_db is not None
        
        # Now query the share record
        share_record = db.session.query(ListShare).filter_by(list_id=list_id_to_share, user_id=shared_user_from_db.id).first()
        assert share_record is not None

    # Now, log in as the shared user and check if they can see the list
    shared_user_client = auth_client_fixture(username='sharedwithuser', password='password') # Use the same client, re-authenticate
    response = shared_user_client.get(url_for('main.dashboard'))
    assert response.status_code == 200
    assert b'Shared List Test' in response.data # Shared list should be on their dashboard

    response = shared_user_client.get(url_for('main.list_detail', list_id=list_id_to_share))
    assert response.status_code == 200 # Shared user should be able to view details
    assert b'Shared List Test' in response.data

def test_access_controls(auth_client_fixture, create_user_fixture, app, db):
    """Test access controls for lists not owned or shared."""
    owner_client = auth_client_fixture(username='owner1')
    other_user_client = auth_client_fixture(username='otheruser')
    
    list_id_owned_by_owner1 = None
    with app.app_context():
        owner1_user = get_user(db.session, 'owner1')
        # Owner1 creates a list
        owned_list = ShoppingList(name='Owner1s Private List', owner_id=owner1_user.id)
        db.session.add(owned_list)
        db.session.commit()
        list_id_owned_by_owner1 = owned_list.id

    # Otheruser tries to access Owner1's list detail page
    response = other_user_client.get(url_for('main.list_detail', list_id=list_id_owned_by_owner1), follow_redirects=False)
    assert response.status_code == 302  # Check for redirection status code
    assert url_for('main.dashboard') in response.location  # Check redirection target
    
    # Follow the redirect and check the dashboard is shown
    response = other_user_client.get(url_for('main.list_detail', list_id=list_id_owned_by_owner1), follow_redirects=True)
    assert response.status_code == 200
    assert url_for('main.dashboard') in response.request.path  # Should be redirected to dashboard

    # Otheruser tries to add an item to Owner1's list (should be blocked by list_detail access first)
    response = other_user_client.post(url_for('main.list_detail', list_id=list_id_owned_by_owner1), 
                                    data={'item_name': 'Sneaky Item'}, 
                                    follow_redirects=False)
    assert response.status_code == 302  # Check for redirection status code
    assert url_for('main.dashboard') in response.location  # Check redirection target

    # Create an item in Owner1's list
    item_in_owner1_list_id = None
    with app.app_context():
        owner1_user = get_user(db.session, 'owner1')
        item = ListItem(item_name='Owner1s Item', list_id=list_id_owned_by_owner1, added_by_id=owner1_user.id)
        db.session.add(item)
        db.session.commit()
        item_in_owner1_list_id = item.id

    # Otheruser tries to delete an item from Owner1's list
    response = other_user_client.post(url_for('main.delete_item', item_id=item_in_owner1_list_id), follow_redirects=False)
    assert response.status_code == 302  # Check for redirection status code
    assert url_for('main.dashboard') in response.location  # Check redirection target

    # Otheruser tries to share Owner1's list
    response = other_user_client.post(url_for('main.share_list', list_id=list_id_owned_by_owner1),
                                    data={'share_with_username': 'anotherrandomuser'},
                                    follow_redirects=False)
    assert response.status_code == 302  # Check for redirection status code
    # For share_list, it redirects back to the list detail page
    assert url_for('main.list_detail', list_id=list_id_owned_by_owner1) in response.location
