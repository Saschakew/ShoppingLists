import unittest
import time
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from flask_testing import LiveServerTestCase

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shopping_list_app.app import create_app
from shopping_list_app.models import db, User, ShoppingList, ListItem

class OfflineE2ETestCase(LiveServerTestCase):
    def create_app(self):
        app = create_app({'TESTING': True})
        app.config['TESTING'] = True
        app.config['LIVESERVER_PORT'] = 8943
        app.config['LIVESERVER_TIMEOUT'] = 10
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_e2e.db'
        app.config['WTF_CSRF_ENABLED'] = False
        return app
    
    def setUp(self):
        db.create_all()
        
        # Create test user
        self.test_user = User(username='testuser')
        self.test_user.set_password('password')
        db.session.add(self.test_user)
        
        # Create test shopping list
        self.test_list = ShoppingList(name='E2E Test List', owner_id=1)
        db.session.add(self.test_list)
        db.session.commit()
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Initialize Chrome WebDriver
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def tearDown(self):
        self.driver.quit()
        db.session.remove()
        db.drop_all()
        os.remove('test_e2e.db')
        
    def login(self):
        self.driver.get(f"{self.get_server_url()}/auth/login")
        
        # Fill in login form
        email_input = self.wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_input.send_keys("test@example.com")
        
        password_input = self.driver.find_element(By.NAME, "password")
        password_input.send_keys("password")
        
        # Submit form
        password_input.submit()
        
        # Wait for redirect to complete
        self.wait.until(EC.url_contains("/dashboard"))
        
    def test_online_add_item(self):
        """Test adding an item while online"""
        self.login()
        
        # Navigate to list detail page
        self.driver.get(f"{self.get_server_url()}/list/{self.test_list.id}")
        
        # Wait for page to load
        self.wait.until(EC.presence_of_element_located((By.ID, "add-item-form")))
        
        # Add an item
        item_input = self.driver.find_element(By.ID, "item_name")
        item_input.send_keys("Online Test Item")
        
        # Submit form
        item_input.submit()
        
        # Wait for item to appear
        self.wait.until(EC.presence_of_element_located((By.XPATH, "//li[contains(text(), 'Online Test Item')]")))
        
        # Verify item exists in the DOM
        items = self.driver.find_elements(By.XPATH, "//li[contains(text(), 'Online Test Item')]")
        self.assertEqual(len(items), 1)
        
        # Verify item was added to database
        item = ListItem.query.filter_by(item_name="Online Test Item").first()
        self.assertIsNotNone(item)
        
    def test_offline_add_item(self):
        """Test adding an item while offline"""
        self.login()
        
        # Navigate to list detail page
        self.driver.get(f"{self.get_server_url()}/list/{self.test_list.id}")
        
        # Wait for page to load
        self.wait.until(EC.presence_of_element_located((By.ID, "add-item-form")))
        
        # Simulate going offline
        self.driver.execute_script("navigator.onLine = false; window.dispatchEvent(new Event('offline'));")
        
        # Wait for offline indicator
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#connection-status.offline")))
        
        # Add an item while offline
        item_input = self.driver.find_element(By.ID, "item_name")
        item_input.send_keys("Offline Test Item")
        
        # Submit form
        item_input.submit()
        
        # Wait for item to appear with offline class
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".offline-item")))
        
        # Verify offline item exists in the DOM
        offline_items = self.driver.find_elements(By.CSS_SELECTOR, ".offline-item")
        self.assertEqual(len(offline_items), 1)
        self.assertIn("Offline Test Item", offline_items[0].text)
        
        # Verify queue badge shows 1 item
        queue_badge = self.driver.find_element(By.ID, "queue-badge")
        self.assertEqual(queue_badge.text, "1")
        
        # Verify item is NOT in database yet
        item = ListItem.query.filter_by(item_name="Offline Test Item").first()
        self.assertIsNone(item)
        
        # Simulate going back online
        self.driver.execute_script("navigator.onLine = true; window.dispatchEvent(new Event('online'));")
        
        # Wait for online indicator
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#connection-status.online")))
        
        # Wait for sync to complete (queue badge to disappear)
        self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "#queue-badge[style*='display: inline-block']")))
        
        # Verify item is now in database
        time.sleep(1)  # Give a moment for the sync to complete
        item = ListItem.query.filter_by(item_name="Offline Test Item").first()
        self.assertIsNotNone(item)
        
    def test_offline_delete_item(self):
        """Test deleting an item while offline"""
        # Add an item to delete
        item = ListItem(item_name="Item To Delete", category="Other", list_id=self.test_list.id, added_by_id=self.test_user.id)
        db.session.add(item)
        db.session.commit()
        
        self.login()
        
        # Navigate to list detail page
        self.driver.get(f"{self.get_server_url()}/list/{self.test_list.id}")
        
        # Wait for page to load and item to be visible
        self.wait.until(EC.presence_of_element_located((By.XPATH, "//li[contains(text(), 'Item To Delete')]")))
        
        # Simulate going offline
        self.driver.execute_script("navigator.onLine = false; window.dispatchEvent(new Event('offline'));")
        
        # Wait for offline indicator
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#connection-status.offline")))
        
        # Find and click delete button for the item
        delete_button = self.driver.find_element(By.XPATH, "//li[contains(text(), 'Item To Delete')]//button[contains(@class, 'delete-item')]")
        delete_button.click()
        
        # Wait for item to be marked as pending delete
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".pending-delete")))
        
        # Verify queue badge shows 1 item
        queue_badge = self.driver.find_element(By.ID, "queue-badge")
        self.assertEqual(queue_badge.text, "1")
        
        # Verify item is still in database
        db_item = ListItem.query.filter_by(item_name="Item To Delete").first()
        self.assertIsNotNone(db_item)
        
        # Simulate going back online
        self.driver.execute_script("navigator.onLine = true; window.dispatchEvent(new Event('online'));")
        
        # Wait for online indicator
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#connection-status.online")))
        
        # Wait for sync to complete (queue badge to disappear)
        self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "#queue-badge[style*='display: inline-block']")))
        
        # Verify item is deleted from database
        time.sleep(1)  # Give a moment for the sync to complete
        db_item = ListItem.query.filter_by(item_name="Item To Delete").first()
        self.assertIsNone(db_item)
        
    def test_page_visibility_change(self):
        """Test page visibility change triggers update check"""
        # Add an item while the page is hidden
        self.login()
        
        # Navigate to list detail page
        self.driver.get(f"{self.get_server_url()}/list/{self.test_list.id}")
        
        # Wait for page to load
        self.wait.until(EC.presence_of_element_located((By.ID, "add-item-form")))
        
        # Simulate page becoming hidden
        self.driver.execute_script("document.visibilityState = 'hidden'; document.dispatchEvent(new Event('visibilitychange'));")
        
        # Add an item to the database directly (simulating another client adding it)
        new_item = ListItem(item_name="Added While Hidden", category="Produce", list_id=self.test_list.id, added_by_id=self.test_user.id)
        db.session.add(new_item)
        db.session.commit()
        
        # Simulate page becoming visible again
        self.driver.execute_script("document.visibilityState = 'visible'; document.dispatchEvent(new Event('visibilitychange'));")
        
        # Wait for the update to be fetched and item to appear
        self.wait.until(EC.presence_of_element_located((By.XPATH, "//li[contains(text(), 'Added While Hidden')]")))
        
        # Verify item is visible in the UI
        items = self.driver.find_elements(By.XPATH, "//li[contains(text(), 'Added While Hidden')]")
        self.assertEqual(len(items), 1)
        
    def test_reconnection_after_server_restart(self):
        """Test reconnection after server restart"""
        self.login()
        
        # Navigate to list detail page
        self.driver.get(f"{self.get_server_url()}/list/{self.test_list.id}")
        
        # Wait for page to load
        self.wait.until(EC.presence_of_element_located((By.ID, "add-item-form")))
        
        # Simulate server disconnect
        self.driver.execute_script("socket.disconnect();")
        
        # Wait for offline indicator
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#connection-status.offline")))
        
        # Add an item while disconnected
        item_input = self.driver.find_element(By.ID, "item_name")
        item_input.send_keys("Disconnected Item")
        item_input.submit()
        
        # Verify offline item appears
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".offline-item")))
        
        # Simulate server reconnect
        self.driver.execute_script("socket.connect();")
        
        # Wait for online indicator
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#connection-status.online")))
        
        # Wait for sync to complete
        self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "#queue-badge[style*='display: inline-block']")))
        
        # Verify item is in database
        time.sleep(1)  # Give a moment for the sync to complete
        item = ListItem.query.filter_by(item_name="Disconnected Item").first()
        self.assertIsNotNone(item)

if __name__ == '__main__':
    unittest.main()
