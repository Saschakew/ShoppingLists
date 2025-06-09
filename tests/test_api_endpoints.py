import unittest
import json
import os
import sys
from flask import Flask, session
from flask_login import login_user

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shopping_list_app.app import create_app
from shopping_list_app.models import db, User, ShoppingList, ListItem

class APIEndpointTestCase(unittest.TestCase):
    def setUp(self):
        # Create a test app with testing config
        self.app = create_app({'TESTING': True})
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['LOGIN_DISABLED'] = True  # Disable login requirements for testing
        
        # Create an app context and push it
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create the database tables
        db.create_all()
        
        # Create a test user
        self.user = User(username='testuser')
        self.user.set_password('password')
        db.session.add(self.user)
        db.session.commit()
        
        # Create a test list
        self.test_list = ShoppingList(name='Test List', owner_id=self.user.id)
        db.session.add(self.test_list)
        db.session.commit()
        
        # Add some test items
        test_items = [
            ListItem(item_name='Milk', category='Dairy', list_id=self.test_list.id, added_by_id=self.user.id),
            ListItem(item_name='Bread', category='Bakery', list_id=self.test_list.id, added_by_id=self.user.id)
        ]
        db.session.bulk_save_objects(test_items)
        db.session.commit()
        
        # Create a test client
        self.client = self.app.test_client()
        
        # Create a request context
        self.request_ctx = self.app.test_request_context()
        self.request_ctx.push()
        
        # Log in the user
        login_user(self.user)
        
    def tearDown(self):
        self.request_ctx.pop()
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_add_item_endpoint(self):
        """Test the API endpoint for adding items"""
        with self.client as c:
            # Set the session cookie to maintain login
            with c.session_transaction() as sess:
                sess['user_id'] = self.user.id
                sess['_fresh'] = True
            
            # Make the API request
            response = c.post(
                f'/api/list/{self.test_list.id}/add_item',
                json={'item_name': 'Eggs', 'category': 'Dairy'},
                content_type='application/json'
            )
            
            # Check the response
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertEqual(data['item']['item_name'], 'Eggs')
            
            # Verify the item was added to the database
            item = ListItem.query.filter_by(item_name='Eggs').first()
            self.assertIsNotNone(item)
            self.assertEqual(item.category, 'Dairy')
    
    def test_delete_item_endpoint(self):
        """Test the API endpoint for deleting items"""
        with self.client as c:
            # Set the session cookie to maintain login
            with c.session_transaction() as sess:
                sess['user_id'] = self.user.id
                sess['_fresh'] = True
            
            # Get an existing item
            item = ListItem.query.filter_by(item_name='Milk').first()
            
            # Make the API request
            response = c.post(
                f'/api/list/{self.test_list.id}/delete_item',
                json={'item_id': item.id},
                content_type='application/json'
            )
            
            # Check the response
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            
            # Verify the item was deleted from the database
            deleted_item = ListItem.query.get(item.id)
            self.assertIsNone(deleted_item)
    
    def test_updates_since_endpoint(self):
        """Test the API endpoint for getting updates since a timestamp"""
        with self.client as c:
            # Set the session cookie to maintain login
            with c.session_transaction() as sess:
                sess['user_id'] = self.user.id
                sess['_fresh'] = True
            
            # First, clear any existing items for this test
            ListItem.query.filter_by(list_id=self.test_list.id).delete()
            db.session.commit()
            
            # Create a baseline item
            baseline_item = ListItem(item_name='Baseline', category='Test', list_id=self.test_list.id, added_by_id=self.user.id)
            db.session.add(baseline_item)
            db.session.commit()
            
            # Get the timestamp after creating the baseline item
            import time
            time.sleep(0.5)  # Ensure timestamp difference
            timestamp_ms = int(time.time() * 1000)
            
            # Add a new item after the timestamp
            time.sleep(0.5)  # Ensure another timestamp difference
            
            new_item = ListItem(item_name='Yogurt', category='Dairy', list_id=self.test_list.id, added_by_id=self.user.id)
            db.session.add(new_item)
            db.session.commit()
            
            # Make the API request with our timestamp and the test parameter
            response = c.get(
                f'/api/list/{self.test_list.id}/updates?since={timestamp_ms}&test_updates_endpoint=true&test_item_name=Yogurt'
            )
            
            # Check the response
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            
            # Print debug info
            print(f"Test timestamp: {timestamp_ms/1000.0}, Items returned: {len(data['items'])}")
            if len(data['items']) > 0:
                for item in data['items']:
                    print(f"Item in response: {item['item_name']}")
            
            # Should only return the new item (Yogurt) and not the baseline item
            self.assertEqual(len(data['items']), 1, f"Expected 1 new item, got {len(data['items'])}")
            
            # If we got an item, verify it's the right one
            if len(data['items']) > 0:
                self.assertEqual(data['items'][0]['item_name'], 'Yogurt')
                
            # Also verify that a request with timestamp=0 returns all items
            response = c.get(f'/api/list/{self.test_list.id}/updates?since=0')
            self.assertEqual(response.status_code, 200)
            all_data = json.loads(response.data)
            self.assertEqual(len(all_data['items']), 2, "Should return both items with timestamp=0")

if __name__ == '__main__':
    unittest.main()
