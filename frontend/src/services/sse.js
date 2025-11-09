/**
 * Server-Sent Events (SSE) Client for Real-time Updates
 * Replaces WebSocket connection with SSE streaming
 */

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const DEFAULT_TENANT = 'hackathon-demo';

class SSEClient {
  constructor(tenantId = DEFAULT_TENANT) {
    this.tenantId = tenantId;
    this.eventSource = null;
    this.listeners = new Map();
    this.reconnectDelay = 1000;
    this.maxReconnectDelay = 30000;
  }

  connect() {
    if (this.eventSource) {
      return; // Already connected
    }

    const url = `${BACKEND_URL}/api/stream/events/${this.tenantId}`;
    this.eventSource = new EventSource(url);

    this.eventSource.onopen = () => {
      console.log('SSE Connected');
      this.reconnectDelay = 1000; // Reset reconnect delay on successful connection
    };

    this.eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleEvent(data);
      } catch (error) {
        console.error('Error parsing SSE message:', error);
      }
    };

    this.eventSource.onerror = (error) => {
      console.error('SSE Error:', error);
      this.eventSource.close();
      this.eventSource = null;

      // Reconnect with exponential backoff
      setTimeout(() => {
        this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay);
        this.connect();
      }, this.reconnectDelay);
    };
  }

  disconnect() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }

  handleEvent(data) {
    const { type } = data;

    // Handle built-in event types
    if (type === 'connected') {
      console.log('SSE connection established for tenant:', data.tenant_id);
      return;
    }

    if (type === 'ping') {
      // Keepalive ping, no action needed
      return;
    }

    // Notify all listeners for this event type
    const listeners = this.listeners.get(type) || [];
    listeners.forEach((callback) => {
      try {
        callback(data);
      } catch (error) {
        console.error(`Error in SSE listener for ${type}:`, error);
      }
    });

    // Also notify wildcard listeners
    const wildcardListeners = this.listeners.get('*') || [];
    wildcardListeners.forEach((callback) => {
      try {
        callback(data);
      } catch (error) {
        console.error('Error in SSE wildcard listener:', error);
      }
    });
  }

  /**
   * Subscribe to events of a specific type
   * @param {string} eventType - Event type to listen for ('patient', 'task', 'document', etc.) or '*' for all events
   * @param {function} callback - Function to call when event is received
   * @returns {function} Unsubscribe function
   */
  on(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType).push(callback);

    // Return unsubscribe function
    return () => {
      const listeners = this.listeners.get(eventType);
      if (listeners) {
        const index = listeners.indexOf(callback);
        if (index > -1) {
          listeners.splice(index, 1);
        }
      }
    };
  }

  /**
   * Remove all listeners for an event type
   * @param {string} eventType - Event type to clear
   */
  off(eventType) {
    this.listeners.delete(eventType);
  }
}

// Create singleton instance
const sseClient = new SSEClient();

export default sseClient;
