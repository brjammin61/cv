import Pusher from 'pusher';
import PusherClient from 'pusher-js';

// Server-side Pusher instance
export const pusherServer = new Pusher({
  appId: process.env.PUSHER_APP_ID!,
  key: process.env.NEXT_PUBLIC_PUSHER_KEY!,
  secret: process.env.PUSHER_SECRET!,
  cluster: process.env.NEXT_PUBLIC_PUSHER_CLUSTER!,
  useTLS: true,
});

// Client-side Pusher instance (for use in components)
export function getPusherClient() {
  return new PusherClient(process.env.NEXT_PUBLIC_PUSHER_KEY!, {
    cluster: process.env.NEXT_PUBLIC_PUSHER_CLUSTER!,
  });
}

// Trigger real-time events
export async function triggerEvent(channel: string, event: string, data: any) {
  await pusherServer.trigger(channel, event, data);
}

// Send real-time message
export async function sendRealtimeMessage(userId: string, message: any) {
  await triggerEvent(`user-${userId}`, 'new-message', message);
}

// Send real-time notification
export async function sendRealtimeNotification(userId: string, notification: any) {
  await triggerEvent(`user-${userId}`, 'notification', notification);
}
