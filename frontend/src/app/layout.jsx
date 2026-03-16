import ClientLenis from "@/components/clientlenis";
import { PipelineProvider } from "@/context/PipelineContext";
import "./globals.css";

export const metadata = {
  title: "CustomsGateways Pipeline",
  description: "AI-powered customs data optimization pipeline",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Epilogue:ital,wght@0,100..900;1,100..900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased">
        <ClientLenis />
        <PipelineProvider>{children}</PipelineProvider>
      </body>
    </html>
  );
}
