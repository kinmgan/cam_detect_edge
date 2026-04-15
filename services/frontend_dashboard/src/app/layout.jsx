import './globals.css'

export const metadata = {
  title: 'AI Camera Dashboard',
  description: 'Edge Computing',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}