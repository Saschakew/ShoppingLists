import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys
import tempfile

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shopping_list_app.app import create_app
from shopping_list_app.models import db, User, ShoppingList, ListItem

class OfflineFunctionalityTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({'TESTING': True})
        self.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create a temporary database
        self.db_fd, self.app.config['DATABASE'] = tempfile.mkstemp()
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + self.app.config['DATABASE']
        self.app.config['TESTING'] = True
        
        # Setup the database
        db.create_all()
        
        # Create a test user
        self.test_user = User(username='testuser')
        self.test_user.set_password('password')
        db.session.add(self.test_user)
        
        # Create a test list
        self.test_list = ShoppingList(name='Test List', owner_id=1)
        db.session.add(self.test_list)
        
        db.session.commit()
        
        # Setup the test client
        self.client = self.app.test_client()
        
        # Login the test user - with session handling
        with self.client.session_transaction() as sess:
            sess['_fresh'] = True  # Mark the session as fresh
        
        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password'
        }, follow_redirects=True)
        
        # Verify login was successful
        self.assertIn(b'Welcome', response.data)
        
        # Create some items for the list
        items = [
            ListItem(item_name='Milk', category='Dairy', list_id=1, added_by_id=1),
            ListItem(item_name='Bread', category='Bakery', list_id=1, added_by_id=1)
        ]
        db.session.bulk_save_objects(items)
        db.session.commit()
        
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        os.close(self.db_fd)
        os.unlink(self.app.config['DATABASE'])
        
    def login(self):
        return self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password'
        }, follow_redirects=True)
        
    def test_api_add_item_endpoint(self):
        """Test the API endpoint for adding items"""
        self.login()
        
        # Add an item via API
        response = self.client.post(
            f'/api/list/{self.test_list.id}/add_item',
            json={'item_name': 'Eggs', 'category': 'Dairy'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('item', data)
        self.assertEqual(data['item']['item_name'], 'Eggs')
        
        # Verify item was added to database
        item = ListItem.query.filter_by(item_name='Eggs').first()
        self.assertIsNotNone(item)
        self.assertEqual(item.category, 'Dairy')
        
    def test_api_delete_item_endpoint(self):
        """Test the API endpoint for deleting items"""
        self.login()
        
        # Get an existing item
        item = ListItem.query.filter_by(item_name='Milk').first()
        
        # Delete the item via API
        response = self.client.post(
            f'/api/list/{self.test_list.id}/delete_item',
            json={'item_id': item.id}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Verify item was deleted from database
        deleted_item = ListItem.query.get(item.id)
        self.assertIsNone(deleted_item)
        
    def test_api_updates_since_endpoint(self):
        """Test the API endpoint for getting updates since a timestamp"""
        self.login()
        
        # Add a new item
        new_item = ListItem(item_name='Cheese', category='Dairy', list_id=self.test_list.id, added_by_id=self.test_user.id)
        db.session.add(new_item)
        db.session.commit()
        
        # Get updates since beginning of time
        response = self.client.get(
            f'/api/list/{self.test_list.id}/updates?since=0'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('items', data)
        
        # Should return all items (3)
        self.assertEqual(len(data['items']), 3)
        
        # Get the timestamp from the response
        timestamp = data['timestamp']
        
        # Add another item
        another_item = ListItem(item_name='Yogurt', category='Dairy', list_id=self.test_list.id, added_by_id=self.test_user.id)
        db.session.add(another_item)
        db.session.commit()
        
        # Get updates since the last timestamp
        response = self.client.get(
            f'/api/list/{self.test_list.id}/updates?since={timestamp}'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Should only return the new item (1)
        self.assertEqual(len(data['items']), 1)
        self.assertEqual(data['items'][0]['item_name'], 'Yogurt')

class OfflineManagerJSTestCase(unittest.TestCase):
    """Test cases for the JavaScript OfflineManager class"""
    
    def setUp(self):
        self.app = create_app({'TESTING': True})
        self.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create a temporary database
        self.db_fd, self.app.config['DATABASE'] = tempfile.mkstemp()
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + self.app.config['DATABASE']
        self.app.config['TESTING'] = True
        
        # Create the database and tables
        db.create_all()
        
        # Create a test user and list
        self.test_user = User(username='testuser')
        self.test_user.set_password('password')
        db.session.add(self.test_user)
        
        self.test_list = ShoppingList(name='Test List', owner_id=1)
        db.session.add(self.test_list)
        
        db.session.commit()
        
        # Setup the test client
        self.client = self.app.test_client()
        
        # Login the test user - with session handling
        with self.client.session_transaction() as sess:
            sess['_fresh'] = True  # Mark the session as fresh
        
        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password'
        }, follow_redirects=True)
        
        # Verify login was successful
        self.assertIn(b'Welcome', response.data)
        
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        os.close(self.db_fd)
        os.unlink(self.app.config['DATABASE'])
    
    def login(self):
        return self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password'
        }, follow_redirects=True)

    @patch('shopping_list_app.main.socketio')
    def test_offline_online_transition_integration(self, mock_socketio):
        """Test the full offline to online transition flow"""
        self.login()
        
        # 1. User visits list page
        response = self.client.get(f'/list/{self.test_list.id}')
        self.assertEqual(response.status_code, 200)
        
        # 2. User goes offline and adds items
        # This would happen in JavaScript, but we'll simulate by directly calling the API
        # with the offline queue data when they come back online
        
        # 3. User comes back online and syncs offline changes
        offline_items = [
            {'item_name': 'Offline Item 1', 'category': 'Other', 'temp_id': 'temp_1'},
            {'item_name': 'Offline Item 2', 'category': 'Produce', 'temp_id': 'temp_2'}
        ]
        
        for item in offline_items:
            response = self.client.post(
                f'/api/list/{self.test_list.id}/add_item',
                json={'item_name': item['item_name'], 'category': item['category']}
            )
            self.assertEqual(response.status_code, 200)
        
        # 4. Verify items were added to the database
        for item in offline_items:
            db_item = ListItem.query.filter_by(item_name=item['item_name']).first()
            self.assertIsNotNone(db_item)
            self.assertEqual(db_item.category, item['category'])
        
        # 5. Check that we can get updates since a timestamp
        response = self.client.get(f'/api/list/{self.test_list.id}/updates?since=0')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Should have both offline items
        self.assertEqual(len(data['items']), 2)
        item_names = [item['item_name'] for item in data['items']]
        self.assertIn('Offline Item 1', item_names)
        self.assertIn('Offline Item 2', item_names)

if __name__ == '__main__':
    unittest.main()
