import type { Metadata } from 'next';
import './globals.css';
import './workspace.css';
export const metadata: Metadata = {
  title: 'Verdant — Document workspace',
  description: 'Find, read and collaborate on company documents.',
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
