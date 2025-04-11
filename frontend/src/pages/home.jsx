import { useEffect, useState } from "react";
import Sidebar from "../components/sidebar";
import ChatComponent from "../components/chatComponent";
import Navbar from "../components/navbar";
import { motion } from "framer-motion";

function Home() {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulated loading time — replace this with actual data load check if needed
    const timeout = setTimeout(() => {
      setIsLoading(false);
    }, 1000);
    return () => clearTimeout(timeout);
  }, []);

  return (
    <div className="bg-[#1f1f24] fixed top-[10vh] left-0 h-[90vh] w-screen text-white">
      {isLoading ? (
        <div className="flex items-center justify-center h-full bg-[#1f1f24]">
          <motion.div
            className="w-14 h-14 border-4 border-[#3b82f6] border-t-transparent rounded-full"
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, ease: "linear", duration: 1 }}
          />
        </div>
      ) : (
        <>
          <Navbar />
          <Sidebar />
          <ChatComponent />
        </>
      )}
    </div>
  );
}

export default Home;
