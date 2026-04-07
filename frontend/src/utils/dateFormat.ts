const MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

export function formatTicketDate(createdAt: string | undefined): string {
  if (!createdAt) return '';
  const date = new Date(createdAt);
  const now = new Date();
  const currentYear = now.getFullYear();
  const isToday = date.getFullYear() === now.getFullYear() && date.getMonth() === now.getMonth() && date.getDate() === now.getDate();
  if (isToday) return 'Today';
  const day = date.getDate();
  const month = MONTH_NAMES[date.getMonth()];
  return date.getFullYear() === currentYear ? `${day} ${month}` : `${day} ${month} ${date.getFullYear()}`;
}
