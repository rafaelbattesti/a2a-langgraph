import type { Metadata } from "next";
import { A2ARuntimeProvider } from "@/app/runtime";

import "./globals.css";

export const metadata: Metadata = {
  title: "assistant-ui + A2A",
  description: "A2A protocol integration with assistant-ui",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-dvh">
      <body className="h-dvh font-sans">
        <A2ARuntimeProvider>{children}</A2ARuntimeProvider>
      </body>
    </html>
  );
}
