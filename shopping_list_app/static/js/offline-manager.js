// Offline Manager for Shopping List App

class OfflineManager {
    constructor(listId, currentUserId) {
        this.listId = listId;
        this.currentUserId = currentUserId;
        this.offlineQueue = [];
        this.lastSyncTimestamp = Date.now();
        this.isOnline = navigator.onLine;
        
        // Load any existing offline queue from localStorage
        this.loadOfflineQueue();
        
        // Set up event listeners for online/offline status
        window.addEventListener('online', () => this.handleOnlineStatusChange(true));
        window.addEventListener('offline', () => this.handleOnlineStatusChange(false));
        
        // Update UI based on current status
        this.updateOfflineStatusUI();
    }
    
    // Save the offline queue to localStorage
    saveOfflineQueue() {
        const queueKey = `offline_queue_list_${this.listId}`;
        localStorage.setItem(queueKey, JSON.stringify(this.offlineQueue));
    }
    
    // Load the offline queue from localStorage
    loadOfflineQueue() {
        const queueKey = `offline_queue_list_${this.listId}`;
        const savedQueue = localStorage.getItem(queueKey);
        if (savedQueue) {
            try {
                this.offlineQueue = JSON.parse(savedQueue);
            } catch (e) {
                console.error('Failed to parse offline queue:', e);
                this.offlineQueue = [];
            }
        }
    }
    
    // Handle online/offline status changes
    handleOnlineStatusChange(isOnline) {
        this.isOnline = isOnline;
        this.updateOfflineStatusUI();
        
        if (isOnline) {
            this.showNotification('You are back online. Syncing changes...', 'info');
            this.syncOfflineChanges();
        } else {
            this.showNotification('You are offline. Changes will be saved locally and synced when you reconnect.', 'warning');
        }
    }
    
    // Update UI to show offline/online status
    updateOfflineStatusUI() {
        const navStatus = document.getElementById('connection-status-nav');
        if (navStatus) {
            const dot = navStatus.querySelector('.status-dot');
            const text = navStatus.querySelector('.status-text');
            if (dot) {
                dot.classList.remove('status-online', 'status-offline');
                dot.classList.add(this.isOnline ? 'status-online' : 'status-offline');
            }
            if (text) {
                text.textContent = this.isOnline ? 'Online' : 'Offline';
                text.classList.remove('online', 'offline');
                text.classList.add(this.isOnline ? 'online' : 'offline');
            }
            // Handle queue badge
            let queueBadge = navStatus.querySelector('#queue-badge');
            if (this.offlineQueue.length > 0) {
                if (!queueBadge) {
                    queueBadge = document.createElement('span');
                    queueBadge.id = 'queue-badge';
                    queueBadge.className = 'queue-badge';
                    navStatus.appendChild(queueBadge);
                }
                queueBadge.textContent = this.offlineQueue.length;
            } else if (queueBadge) {
                queueBadge.remove();
            }
        }
    }
    
    // Queue an item to be added when back online
    queueAddItem(itemName, category) {
        const offlineItem = {
            type: 'add',
            data: {
                item_name: itemName,
                category: category,
                list_id: this.listId,
                added_by_id: this.currentUserId,
                temp_id: `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                timestamp: Date.now()
            }
        };
        
        this.offlineQueue.push(offlineItem);
        this.saveOfflineQueue();
        this.updateOfflineStatusUI();
        
        // Return the temp ID so we can use it for local UI updates
        return offlineItem.data.temp_id;
    }
    
    // Queue an item to be deleted when back online
    queueDeleteItem(itemId, isTemp = false) {
        // If it's a temporary item that hasn't been synced, just remove it from the queue
        if (isTemp) {
            this.offlineQueue = this.offlineQueue.filter(item => 
                !(item.type === 'add' && item.data.temp_id === itemId)
            );
            this.saveOfflineQueue();
            this.updateOfflineStatusUI();
            return;
        }
        
        // Otherwise queue the deletion for when we're back online
        const offlineItem = {
            type: 'delete',
            data: {
                item_id: itemId,
                list_id: this.listId,
                timestamp: Date.now()
            }
        };
        
        this.offlineQueue.push(offlineItem);
        this.saveOfflineQueue();
        this.updateOfflineStatusUI();
    }
    
    // Process the offline queue when back online
    async syncOfflineChanges() {
        if (!this.isOnline || this.offlineQueue.length === 0) {
            return;
        }
        
        this.showNotification(`Syncing ${this.offlineQueue.length} changes...`, 'info');
        
        // Sort by timestamp to process in order
        this.offlineQueue.sort((a, b) => a.data.timestamp - b.data.timestamp);
        
        const failedItems = [];
        
        for (const item of this.offlineQueue) {
            try {
                if (item.type === 'add') {
                    await this.syncAddItem(item.data);
                } else if (item.type === 'delete') {
                    await this.syncDeleteItem(item.data);
                }
            } catch (error) {
                console.error(`Failed to sync item:`, item, error);
                failedItems.push(item);
            }
        }
        
        // Update the queue with only failed items
        this.offlineQueue = failedItems;
        this.saveOfflineQueue();
        this.updateOfflineStatusUI();
        
        if (failedItems.length > 0) {
            this.showNotification(`Failed to sync ${failedItems.length} changes. Will retry later.`, 'error');
        } else {
            this.showNotification('All changes synced successfully!', 'success');
            // Update the last sync timestamp
            this.lastSyncTimestamp = Date.now();
            localStorage.setItem(`last_sync_list_${this.listId}`, this.lastSyncTimestamp);
        }
        
        // Refresh the page to show the latest data
        // We could make this more elegant by just updating the UI, but a refresh is simpler
        // and ensures everything is in sync
        window.location.reload();
    }
    
    // Sync an add item operation with the server
    async syncAddItem(itemData) {
        const formData = new FormData();
        formData.append('item_name', itemData.item_name);
        formData.append('category', itemData.category);
        
        const response = await fetch(`/list/${this.listId}`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (!response.ok) {
            throw new Error(`Failed to add item: ${response.statusText}`);
        }
        
        // Remove the temporary item from the UI
        const tempItem = document.getElementById(`item-${itemData.temp_id}`);
        if (tempItem) {
            tempItem.remove();
        }
        
        return await response.json();
    }
    
    // Sync a delete item operation with the server
    async syncDeleteItem(itemData) {
        const formData = new FormData();
        
        const response = await fetch(`/item/${itemData.item_id}/delete`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (!response.ok) {
            throw new Error(`Failed to delete item: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    // Add an item to the UI locally (for offline mode)
    addItemLocally(itemName, category, tempId) {
        const categorySlug = this.slugifyCategory(category);
        const targetListId = `item-list-${categorySlug}`;
        let itemListUl = document.getElementById(targetListId);
        let categorySectionDiv = document.getElementById(`category-section-${categorySlug}`);
        const shoppingListContainer = document.querySelector('.shopping-list-container');
        const emptyListMessage = document.getElementById('empty-list-message');
        
        // If category section doesn't exist, create it
        if (!categorySectionDiv) {
            categorySectionDiv = document.createElement('div');
            categorySectionDiv.className = 'category-section';
            categorySectionDiv.id = `category-section-${categorySlug}`;

            const categoryTitle = document.createElement('h2');
            categoryTitle.className = 'category-title';
            categoryTitle.textContent = category || 'Other';
            categorySectionDiv.appendChild(categoryTitle);

            itemListUl = document.createElement('ul');
            itemListUl.id = targetListId;
            itemListUl.className = 'items-container category-item-list';
            categorySectionDiv.appendChild(itemListUl);

            // Insert before the empty list message or at the end
            shoppingListContainer.insertBefore(categorySectionDiv, emptyListMessage);
        } else if (!itemListUl) {
            // Section exists but UL is missing (should not happen if created together)
            itemListUl = document.createElement('ul');
            itemListUl.id = targetListId;
            itemListUl.className = 'items-container category-item-list';
            categorySectionDiv.appendChild(itemListUl);
        }
        
        const newItemLi = document.createElement('li');
        newItemLi.id = `item-${tempId}`;
        newItemLi.className = 'item offline-item';
        
        const itemContentDiv = document.createElement('div');
        itemContentDiv.className = 'item-content';
        const itemNameSpan = document.createElement('span');
        itemNameSpan.className = 'item-name';
        itemNameSpan.textContent = itemName;
        itemContentDiv.appendChild(itemNameSpan);
        
        // Add an offline indicator
        const offlineIndicator = document.createElement('span');
        offlineIndicator.className = 'offline-indicator';
        offlineIndicator.textContent = '(offline)';
        itemContentDiv.appendChild(offlineIndicator);
        
        const itemActionsDiv = document.createElement('div');
        itemActionsDiv.className = 'item-actions';
        
        // Add delete button
        const deleteButton = document.createElement('button');
        deleteButton.type = 'button';
        deleteButton.className = 'btn-delete';
        deleteButton.innerHTML = '&#x2715;';
        deleteButton.addEventListener('click', () => {
            this.queueDeleteItem(tempId, true);
            newItemLi.remove();
            
            // Check if the list is empty and update UI accordingly
            if (itemListUl.children.length === 0) {
                let hasAnyItems = false;
                const allCategoryLists = document.querySelectorAll('.category-item-list');
                allCategoryLists.forEach(ul => {
                    if (ul.children.length > 0) {
                        hasAnyItems = true;
                    }
                });
                
                if (!hasAnyItems && emptyListMessage) {
                    emptyListMessage.style.display = 'block';
                }
            }
        });
        
        itemActionsDiv.appendChild(deleteButton);
        newItemLi.appendChild(itemContentDiv);
        newItemLi.appendChild(itemActionsDiv);
        itemListUl.appendChild(newItemLi);
        
        if (emptyListMessage) emptyListMessage.style.display = 'none';
    }
    
    // Helper function to convert category names to slug format
    slugifyCategory(categoryName) {
        if (!categoryName) return 'other';
        let slug = categoryName.toLowerCase();
        slug = slug.replace(/ & /g, '-and-');
        slug = slug.replace(/ /g, '-');
        return slug;
    }
    
    // Show a notification to the user
    showNotification(message, type = 'info') {
        const flashesContainer = document.querySelector('.flashes') || document.createElement('div');
        
        if (!flashesContainer.classList.contains('flashes')) {
            flashesContainer.className = 'flashes floating-flashes';
            document.body.appendChild(flashesContainer);
        }
        
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} fade-out`;
        notification.textContent = message;
        
        flashesContainer.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
    
    // Get the last sync timestamp
    getLastSyncTimestamp() {
        const savedTimestamp = localStorage.getItem(`last_sync_list_${this.listId}`);
        return savedTimestamp ? parseInt(savedTimestamp) : this.lastSyncTimestamp;
    }
    
    // Request updates since last sync
    async requestUpdatesSinceLastSync() {
        if (!this.isOnline) return;
        
        const timestamp = this.getLastSyncTimestamp();
        try {
            const response = await fetch(`/api/list/${this.listId}/updates?since=${timestamp}`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                throw new Error(`Failed to get updates: ${response.statusText}`);
            }
            
            const updates = await response.json();
            if (updates.changes && updates.changes.length > 0) {
                this.showNotification(`Received ${updates.changes.length} updates since your last sync.`, 'info');
                // Refresh to show the latest data
                window.location.reload();
            }
            
            // Update the last sync timestamp
            this.lastSyncTimestamp = Date.now();
            localStorage.setItem(`last_sync_list_${this.listId}`, this.lastSyncTimestamp);
            
        } catch (error) {
            console.error('Failed to get updates:', error);
        }
    }
}
