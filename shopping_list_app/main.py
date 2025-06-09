from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from .models import db, ShoppingList, ListItem, ListShare, User
from .extensions import socketio # Import socketio from extensions.py

main = Blueprint('main', __name__)

@main.route('/')
def index():
    # This will be the landing page. 
    # If user is logged in, maybe redirect to dashboard, or show a generic home page.
    if current_user.is_authenticated:
        # If user has a favorite list, redirect to it
        if current_user.favorite_list_id:
            return redirect(url_for('main.list_detail', list_id=current_user.favorite_list_id))
        return redirect(url_for('main.dashboard'))
    return render_template('index.html') # We'll need to create index.html

@main.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        list_name = request.form.get('list_name')
        if list_name:
            new_list = ShoppingList(name=list_name, owner_id=current_user.id)
            db.session.add(new_list)
            db.session.commit()
            flash('New shopping list created!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('List name cannot be empty.', 'danger')

    # Fetch lists owned by the user
    owned_lists = ShoppingList.query.filter_by(owner_id=current_user.id).order_by(ShoppingList.created_at.desc()).all()
    
    # Fetch lists shared with the user
    shared_list_ids = [share.list_id for share in ListShare.query.filter_by(user_id=current_user.id).all()]
    shared_lists_objects = ShoppingList.query.filter(ShoppingList.id.in_(shared_list_ids)).order_by(ShoppingList.created_at.desc()).all()
    
    # Combine and ensure no duplicates if a user somehow shares a list with themselves (though UI shouldn't allow)
    # For simplicity, we'll just pass them separately or combine carefully if needed.
    # Here, we'll just show owned lists for now, and add shared list display logic later or combine them.
    # For a more robust solution, you might want to combine and sort all accessible lists.
    
    all_accessible_lists = list(set(owned_lists + shared_lists_objects)) # Using set to remove duplicates if any
    all_accessible_lists.sort(key=lambda x: x.created_at, reverse=True) # Sort them again after combining

    return render_template('dashboard.html', current_user=current_user, lists=all_accessible_lists)


@main.route('/list/<int:list_id>', methods=['GET', 'POST'])
@login_required
def list_detail(list_id):
    list_instance = ShoppingList.query.get_or_404(list_id)

    # Check if the current user has access to this list
    is_owner = list_instance.owner_id == current_user.id
    is_shared_with_user = ListShare.query.filter_by(list_id=list_id, user_id=current_user.id).first() is not None
    
    print(f"DEBUG - Access check for list {list_id}:")
    print(f"DEBUG - Current user: {current_user.id}, List owner: {list_instance.owner_id}")
    print(f"DEBUG - is_owner: {is_owner}, is_shared_with_user: {is_shared_with_user}")

    if not (is_owner or is_shared_with_user):
        print(f"DEBUG - Access denied for user {current_user.id} to list {list_id}")
        flash('You do not have access to this list.', 'danger')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        # This part handles adding a new item or other POST actions for the list
        item_name = request.form.get('item_name')
        category = request.form.get('category', 'Other') # Get category, default to 'Other' if not provided
        if item_name:
            new_item = ListItem(item_name=item_name, category=category, list_id=list_instance.id, added_by_id=current_user.id)
            db.session.add(new_item)
            db.session.commit()
            flash(f'Item "{item_name}" added to {list_instance.name}.', 'success')
            # Emit event to the specific list room
            socketio.emit('item_added', 
                          {'item': {'id': new_item.id, 
                                    'name': new_item.item_name,
                                    'category': new_item.category,
                                    'added_by_username': new_item.adder.username, # Keep username for display
                                    'added_by_id': new_item.added_by_id, # Add ID for logic
                                    'added_at': new_item.added_at.strftime('%Y-%m-%d %H:%M'),
                                    'is_purchased': new_item.is_purchased},
                           'list_id': list_instance.id}, 
                          room=f'list_{list_instance.id}')
            return redirect(url_for('main.list_detail', list_id=list_id))
        else:
            flash('Item name cannot be empty.', 'danger')
    
    # Define predefined categories for ordering and ensuring all are listed
    PREDEFINED_CATEGORIES = [
        "Fruits", "Vegetables", "Dairy", "Bakery", "Meat & Poultry",
        "Fish & Seafood", "Pantry Staples", "Frozen Foods",
        "Beverages", "Household", "Other"
    ]

    items_by_category = {category: [] for category in PREDEFINED_CATEGORIES}
    raw_items = ListItem.query.filter_by(list_id=list_id).order_by(ListItem.added_at.asc()).all()

    for item in raw_items:
        category_key = item.category if item.category in items_by_category else 'Other'
        items_by_category[category_key].append(item)

    return render_template('list_detail.html', list=list_instance,
                           items_by_category=items_by_category,
                           categories_ordered=PREDEFINED_CATEGORIES,
                           current_user=current_user)


@main.route('/item/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    item_to_delete = ListItem.query.get_or_404(item_id)
    list_instance = ShoppingList.query.get_or_404(item_to_delete.list_id)

    # Check if the current user has access to this list to delete items
    is_owner = list_instance.owner_id == current_user.id
    is_shared_with_user = ListShare.query.filter_by(list_id=list_instance.id, user_id=current_user.id).first() is not None

    if not (is_owner or is_shared_with_user):
        flash('You do not have permission to delete items from this list.', 'danger')
        return redirect(url_for('main.dashboard')) # Or perhaps back to where they came from if possible

    item_name = item_to_delete.item_name # Get name for flash message before deleting
    db.session.delete(item_to_delete)
    db.session.commit()
    flash(f'Item "{item_name}" deleted from {list_instance.name}.', 'success')
    # Emit event to the specific list room
    socketio.emit('item_deleted', 
                  {'item_id': item_id, 'list_id': list_instance.id}, 
                  room=f'list_{list_instance.id}')
    return redirect(url_for('main.list_detail', list_id=list_instance.id))


@main.route('/list/<int:list_id>/share', methods=['GET'])
@login_required
def share_list_page(list_id):
    list_to_share = ShoppingList.query.get_or_404(list_id)

    # Check if the current user has access to this list
    is_owner = list_to_share.owner_id == current_user.id
    is_shared_with_user = ListShare.query.filter_by(list_id=list_id, user_id=current_user.id).first() is not None
    
    if not (is_owner or is_shared_with_user):
        flash('You do not have access to this list.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    # Only the owner can see the share page with sharing controls
    can_share = is_owner
    
    return render_template('share_list.html', list=list_to_share, can_share=can_share)

@main.route('/list/<int:list_id>/share', methods=['POST'])
@login_required
def share_list(list_id):
    list_to_share = ShoppingList.query.get_or_404(list_id)

    # Only the owner can share the list
    if list_to_share.owner_id != current_user.id:
        flash('You do not have permission to share this list.', 'danger')
        return redirect(url_for('main.share_list_page', list_id=list_id))

    username_to_share_with = request.form.get('share_with_username')
    if not username_to_share_with:
        flash('Username to share with cannot be empty.', 'warning')
        return redirect(url_for('main.share_list_page', list_id=list_id))

    user_to_share_with = User.query.filter_by(username=username_to_share_with).first()

    if not user_to_share_with:
        flash(f'User "{username_to_share_with}" not found.', 'danger')
        return redirect(url_for('main.share_list_page', list_id=list_id))

    if user_to_share_with.id == current_user.id:
        flash('You cannot share a list with yourself.', 'warning')
        return redirect(url_for('main.share_list_page', list_id=list_id))

    # Check if already shared with this user
    existing_share = ListShare.query.filter_by(list_id=list_id, user_id=user_to_share_with.id).first()
    if existing_share:
        flash(f'This list is already shared with {username_to_share_with}.', 'info')
        return redirect(url_for('main.share_list_page', list_id=list_id))

    new_share = ListShare(list_id=list_id, user_id=user_to_share_with.id)
    db.session.add(new_share)
    db.session.commit()
    flash(f'List "{list_to_share.name}" shared with {username_to_share_with}.', 'success')
    return redirect(url_for('main.share_list_page', list_id=list_id))


@main.route('/list/<int:list_id>/favorite', methods=['POST'])
@login_required
def set_favorite_list(list_id):
    list_instance = ShoppingList.query.get_or_404(list_id)
    
    # Check if the current user has access to this list
    is_owner = list_instance.owner_id == current_user.id
    is_shared_with_user = ListShare.query.filter_by(list_id=list_id, user_id=current_user.id).first() is not None
    
    if not (is_owner or is_shared_with_user):
        flash('You do not have access to this list.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Toggle favorite status
    if current_user.favorite_list_id == list_id:
        # If this list is already the favorite, remove it as favorite
        current_user.favorite_list_id = None
        flash(f'Removed "{list_instance.name}" from favorites.', 'info')
    else:
        # Set this list as the favorite
        current_user.favorite_list_id = list_id
        flash(f'Set "{list_instance.name}" as your favorite list.', 'success')
    
    db.session.commit()
    return redirect(url_for('main.list_detail', list_id=list_id))
