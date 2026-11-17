import { useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

export type SSEStatus = 'connected' | 'connecting' | 'disconnected';

export interface SSEMessage {
  event: string;
  data: any;
  timestamp: string;
}

export function useSSE(onMessage?: (msg: SSEMessage) => void) {
  const [status, setStatus] = useState<SSEStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<SSEMessage | null>(null);
  const queryClient = useQueryClient();

  useEffect(() => {
    let eventSource: EventSource | null = null;
    let reconnectTimeout: any = null;

    function connect() {
      setStatus('connecting');
      eventSource = new EventSource('/api/stream');

      eventSource.onopen = () => {
        setStatus('connected');
      };

      eventSource.onerror = () => {
        setStatus('disconnected');
        if (eventSource) {
          eventSource.close();
        }
        // Attempt reconnect after 5s
        reconnectTimeout = setTimeout(connect, 5000);
      };

      const handleEvent = (event: MessageEvent, eventName: string) => {
        try {
          const parsed = JSON.parse(event.data);
          const msg: SSEMessage = {
            event: eventName,
            data: parsed,
            timestamp: new Date().toISOString(),
          };
          setLastMessage(msg);
          if (onMessage) onMessage(msg);

          // Invalidate relevant queries for seamless live reactivity
          if (['ticket_created', 'ticket_updated', 'feedback_submitted'].includes(eventName)) {
            queryClient.invalidateQueries({ queryKey: ['tickets'] });
            queryClient.invalidateQueries({ queryKey: ['dashboard'] });
          }
          if (['alert_created', 'risk_escalated'].includes(eventName)) {
            queryClient.invalidateQueries({ queryKey: ['alerts'] });
            queryClient.invalidateQueries({ queryKey: ['dashboard'] });
            queryClient.invalidateQueries({ queryKey: ['risk_forecast'] });
          }
        } catch {
          // Ignore parse errors on raw ping
        }
      };

      // Listen for custom server events
      eventSource.addEventListener('ticket_created', (e) => handleEvent(e, 'ticket_created'));
      eventSource.addEventListener('ticket_updated', (e) => handleEvent(e, 'ticket_updated'));
      eventSource.addEventListener('alert_created', (e) => handleEvent(e, 'alert_created'));
      eventSource.addEventListener('risk_escalated', (e) => handleEvent(e, 'risk_escalated'));
      eventSource.addEventListener('feedback_submitted', (e) => handleEvent(e, 'feedback_submitted'));
    }

    connect();

    return () => {
      if (eventSource) eventSource.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, [queryClient, onMessage]);

  return { status, lastMessage };
}
