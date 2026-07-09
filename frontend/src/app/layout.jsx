import "./globals.css";
import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";

export const metadata = {
  title: "CodeRecommend AI",
  description: "Competitive Programming Recommendation System",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="h-screen overflow-hidden bg-slate-950 text-white" suppressHydrationWarning>
        <div className="flex h-full overflow-hidden">
          <Sidebar />

          <div className="flex flex-col flex-1 h-full overflow-hidden">
            <Navbar />

            <main className="flex-1 overflow-y-auto p-8">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
