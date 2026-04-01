import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";

const plusJakarta = Plus_Jakarta_Sans({
  variable: "--font-plus-jakarta",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Travel Optimization Engine",
  description: "AI-powered flight price optimization & route search.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${plusJakarta.variable} font-sans h-full antialiased text-[#171717] bg-[#FFFFFF]`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
