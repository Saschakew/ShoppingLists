// Mock browser environment for testing
const mockLocalStorage = (() => {
    let store = {};
    return {
        getItem: (key) => store[key] || null,
        setItem: (key, value) => { store[key] = value.toString(); },
        removeItem: (key) => { delete store[key]; },
        clear: () => { store = {}; },
        _getStore: () => store
    };
})();

// Mock fetch function
const mockFetch = (response) => {
    return jest.fn().mockImplementation(() => 
        Promise.resolve({
            ok: response.ok || true,
            json: () => Promise.resolve(response.data || {})
        })
    );
};

// Mock DOM elements
const mockDOM = () => {
    document.body.innerHTML = `
        <div id="connection-status"></div>
        <div id="queue-badge"></div>
        <div id="notification-area"></div>
        <div id="items-container">
            <div id="category-Dairy" class="category-section">
                <h3>Dairy</h3>
                <ul class="items-list"></ul>
            </div>
            <div id="category-Produce" class="category-section">
                <h3>Produce</h3>
                <ul class="items-list"></ul>
            </div>
            <div id="category-Other" class="category-section">
                <h3>Other</h3>
                <ul class="items-list"></ul>
            </div>
        </div>
    `;
};

describe('OfflineManager', () => {
    let offlineManager;
    const listId = 123;
    const userId = 456;

    beforeEach(() => {
        // Mock localStorage
        Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });
        localStorage.clear();

        // Mock navigator.onLine
        Object.defineProperty(navigator, 'onLine', { writable: true, value: true });

        // Mock DOM
        mockDOM();

        // Mock fetch
        global.fetch = mockFetch({ data: { success: true } });

        // Create a new instance for each test
        offlineManager = new OfflineManager(listId, userId);
    });

    test('initializes with correct properties', () => {
        expect(offlineManager.listId).toBe(listId);
        expect(offlineManager.userId).toBe(userId);
        expect(offlineManager.isOnline).toBe(true);
        expect(offlineManager.queueKey).toBe(`offline_queue_${listId}`);
        expect(offlineManager.lastSyncKey).toBe(`last_sync_${listId}`);
    });

    test('handles online status change', () => {
        const connectionStatus = document.getElementById('connection-status');
        
        // Test going offline
        offlineManager.handleOnlineStatusChange(false);
        expect(offlineManager.isOnline).toBe(false);
        expect(connectionStatus.textContent).toContain('Offline');
        expect(connectionStatus.classList.contains('offline')).toBe(true);
        
        // Test going online
        global.fetch = mockFetch({ data: { success: true, items: [] } });
        offlineManager.handleOnlineStatusChange(true);
        expect(offlineManager.isOnline).toBe(true);
        expect(connectionStatus.textContent).toContain('Online');
        expect(connectionStatus.classList.contains('online')).toBe(true);
    });

    test('queues add item when offline', () => {
        // Set to offline
        offlineManager.handleOnlineStatusChange(false);
        
        // Queue an item
        const tempId = offlineManager.queueAddItem('Test Item', 'Dairy');
        
        // Check queue in localStorage
        const queue = JSON.parse(localStorage.getItem(offlineManager.queueKey));
        expect(queue.length).toBe(1);
        expect(queue[0].type).toBe('add');
        expect(queue[0].data.item_name).toBe('Test Item');
        expect(queue[0].data.category).toBe('Dairy');
        expect(queue[0].temp_id).toBe(tempId);
        
        // Check queue badge
        const queueBadge = document.getElementById('queue-badge');
        expect(queueBadge.textContent).toBe('1');
        expect(queueBadge.style.display).toBe('inline-block');
    });

    test('queues delete item when offline', () => {
        // Set to offline
        offlineManager.handleOnlineStatusChange(false);
        
        // Queue a delete
        offlineManager.queueDeleteItem(789);
        
        // Check queue in localStorage
        const queue = JSON.parse(localStorage.getItem(offlineManager.queueKey));
        expect(queue.length).toBe(1);
        expect(queue[0].type).toBe('delete');
        expect(queue[0].data.item_id).toBe(789);
        
        // Check queue badge
        const queueBadge = document.getElementById('queue-badge');
        expect(queueBadge.textContent).toBe('1');
    });

    test('adds item locally to the DOM', () => {
        const tempId = 'temp_123';
        offlineManager.addItemLocally('Local Item', 'Dairy', tempId);
        
        // Check if item was added to the DOM
        const dairyList = document.querySelector('#category-Dairy .items-list');
        expect(dairyList.children.length).toBe(1);
        
        const itemElement = dairyList.children[0];
        expect(itemElement.textContent).toContain('Local Item');
        expect(itemElement.classList.contains('offline-item')).toBe(true);
        expect(itemElement.dataset.tempId).toBe(tempId);
    });

    test('syncs queue when going online', async () => {
        // Setup: Add items to queue while offline
        offlineManager.handleOnlineStatusChange(false);
        offlineManager.queueAddItem('Offline Item 1', 'Dairy');
        offlineManager.queueAddItem('Offline Item 2', 'Produce');
        
        // Mock successful API responses
        global.fetch = mockFetch({ 
            data: { 
                success: true, 
                item: { id: 101, item_name: 'Offline Item 1', category: 'Dairy' } 
            } 
        });
        
        // Go online and sync
        await offlineManager.handleOnlineStatusChange(true);
        
        // Queue should be empty after sync
        const queue = JSON.parse(localStorage.getItem(offlineManager.queueKey));
        expect(queue.length).toBe(0);
        
        // Queue badge should be hidden
        const queueBadge = document.getElementById('queue-badge');
        expect(queueBadge.style.display).toBe('none');
    });

    test('handles sync failures', async () => {
        // Setup: Add items to queue while offline
        offlineManager.handleOnlineStatusChange(false);
        offlineManager.queueAddItem('Will Fail', 'Other');
        
        // Mock failed API response
        global.fetch = mockFetch({ 
            ok: false,
            data: { success: false, error: 'API Error' } 
        });
        
        // Go online and attempt sync
        await offlineManager.handleOnlineStatusChange(true);
        
        // Queue should still contain the failed item
        const queue = JSON.parse(localStorage.getItem(offlineManager.queueKey));
        expect(queue.length).toBe(1);
        expect(queue[0].data.item_name).toBe('Will Fail');
        
        // Queue badge should still show
        const queueBadge = document.getElementById('queue-badge');
        expect(queueBadge.textContent).toBe('1');
        expect(queueBadge.style.display).toBe('inline-block');
    });

    test('requests updates since last sync', async () => {
        // Set a last sync timestamp
        const lastSync = Date.now() - 3600000; // 1 hour ago
        localStorage.setItem(offlineManager.lastSyncKey, lastSync.toString());
        
        // Mock API response with new items
        global.fetch = mockFetch({ 
            data: { 
                success: true, 
                items: [
                    { id: 201, item_name: 'New Item 1', category: 'Dairy' },
                    { id: 202, item_name: 'New Item 2', category: 'Produce' }
                ],
                timestamp: Date.now()
            } 
        });
        
        // Request updates
        await offlineManager.requestUpdatesSinceLastSync();
        
        // Check if items were added to DOM
        const dairyList = document.querySelector('#category-Dairy .items-list');
        const produceList = document.querySelector('#category-Produce .items-list');
        
        expect(dairyList.children.length).toBe(1);
        expect(produceList.children.length).toBe(1);
        
        expect(dairyList.children[0].textContent).toContain('New Item 1');
        expect(produceList.children[0].textContent).toContain('New Item 2');
    });

    test('shows notifications', () => {
        offlineManager.showNotification('Test notification', 'info');
        
        const notificationArea = document.getElementById('notification-area');
        expect(notificationArea.children.length).toBe(1);
        expect(notificationArea.children[0].textContent).toBe('Test notification');
        expect(notificationArea.children[0].classList.contains('info')).toBe(true);
        
        // Test auto-removal (would need to mock timers for proper testing)
    });
});

// Integration test scenarios
describe('OfflineManager Integration Scenarios', () => {
    let offlineManager;
    
    beforeEach(() => {
        // Setup mocks
        Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });
        localStorage.clear();
        Object.defineProperty(navigator, 'onLine', { writable: true, value: true });
        mockDOM();
        global.fetch = mockFetch({ data: { success: true } });
        
        // Create instance
        offlineManager = new OfflineManager(123, 456);
    });
    
    test('Scenario: User goes offline, adds items, then comes back online', async () => {
        // 1. User is initially online
        expect(offlineManager.isOnline).toBe(true);
        
        // 2. User goes offline
        navigator.onLine = false;
        offlineManager.handleOnlineStatusChange(false);
        expect(offlineManager.isOnline).toBe(false);
        
        // 3. User adds items while offline
        const tempId1 = offlineManager.queueAddItem('Offline Milk', 'Dairy');
        const tempId2 = offlineManager.queueAddItem('Offline Apples', 'Produce');
        
        // 4. Items appear in UI with offline indicator
        offlineManager.addItemLocally('Offline Milk', 'Dairy', tempId1);
        offlineManager.addItemLocally('Offline Apples', 'Produce', tempId2);
        
        const dairyList = document.querySelector('#category-Dairy .items-list');
        const produceList = document.querySelector('#category-Produce .items-list');
        
        expect(dairyList.children.length).toBe(1);
        expect(produceList.children.length).toBe(1);
        expect(dairyList.children[0].classList.contains('offline-item')).toBe(true);
        expect(produceList.children[0].classList.contains('offline-item')).toBe(true);
        
        // 5. Queue shows 2 pending items
        const queueBadge = document.getElementById('queue-badge');
        expect(queueBadge.textContent).toBe('2');
        
        // 6. Mock successful API responses for when we go online
        let apiCallCount = 0;
        global.fetch = jest.fn().mockImplementation(() => {
            apiCallCount++;
            return Promise.resolve({
                ok: true,
                json: () => Promise.resolve({
                    success: true,
                    item: { id: 100 + apiCallCount, item_name: `Synced Item ${apiCallCount}`, category: 'Dairy' }
                })
            });
        });
        
        // 7. User comes back online
        navigator.onLine = true;
        await offlineManager.handleOnlineStatusChange(true);
        
        // 8. Items should be synced (API called twice)
        expect(apiCallCount).toBe(2);
        
        // 9. Queue should be empty
        const queue = JSON.parse(localStorage.getItem(offlineManager.queueKey));
        expect(queue.length).toBe(0);
        expect(queueBadge.style.display).toBe('none');
    });
    
    test('Scenario: User is offline, deletes items, then comes back online', async () => {
        // Setup: Add some items to the DOM that we can delete
        const dairyList = document.querySelector('#category-Dairy .items-list');
        const item1 = document.createElement('li');
        item1.dataset.id = '301';
        item1.textContent = 'Item to delete';
        dairyList.appendChild(item1);
        
        // 1. User goes offline
        navigator.onLine = false;
        offlineManager.handleOnlineStatusChange(false);
        
        // 2. User deletes an item while offline
        offlineManager.queueDeleteItem(301);
        
        // 3. Item is visually removed or marked
        expect(dairyList.children.length).toBe(1); // Still there but would be visually marked
        
        // 4. Queue shows 1 pending item
        const queueBadge = document.getElementById('queue-badge');
        expect(queueBadge.textContent).toBe('1');
        
        // 5. Mock successful API responses for when we go online
        global.fetch = mockFetch({ data: { success: true } });
        
        // 6. User comes back online
        navigator.onLine = true;
        await offlineManager.handleOnlineStatusChange(true);
        
        // 7. Delete should be synced and queue empty
        const queue = JSON.parse(localStorage.getItem(offlineManager.queueKey));
        expect(queue.length).toBe(0);
        expect(queueBadge.style.display).toBe('none');
    });
    
    test('Scenario: User is offline, performs actions, comes online but sync fails', async () => {
        // 1. User goes offline
        navigator.onLine = false;
        offlineManager.handleOnlineStatusChange(false);
        
        // 2. User adds an item while offline
        offlineManager.queueAddItem('Will Fail To Sync', 'Other');
        
        // 3. Mock failed API response
        global.fetch = mockFetch({ 
            ok: false, 
            data: { success: false, error: 'Server Error' } 
        });
        
        // 4. User comes back online, but sync fails
        navigator.onLine = true;
        await offlineManager.handleOnlineStatusChange(true);
        
        // 5. Queue should still have the item
        const queue = JSON.parse(localStorage.getItem(offlineManager.queueKey));
        expect(queue.length).toBe(1);
        
        // 6. Queue badge should still show
        const queueBadge = document.getElementById('queue-badge');
        expect(queueBadge.textContent).toBe('1');
        expect(queueBadge.style.display).toBe('inline-block');
        
        // 7. Notification should show error
        const notificationArea = document.getElementById('notification-area');
        expect(notificationArea.children.length).toBe(1);
        expect(notificationArea.children[0].classList.contains('error')).toBe(true);
    });
});
