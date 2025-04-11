import { useState } from "react";
import { Send } from "lucide-react";
import { motion } from "framer-motion";

const ChatInput = ({ onSend }) => {
  const [message, setMessage] = useState("");

  const handleSend = async () => {
    if (message.trim()) {
      await onSend(message);
      setMessage("");
    }
  };

  return (
    <div className="fixed bottom-4 w-[70vw] left-[60vw] -translate-x-1/2 z-20">
      <div className="flex items-center gap-2 bg-[#2a2a2e] border border-[#333] shadow-md px-4 py-2 rounded-2xl backdrop-blur-md">
        <input
          type="text"
          className="flex-1 bg-transparent text-white placeholder-gray-400 outline-none px-2 py-2 rounded-md"
          placeholder="Type your message..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />
        <motion.button
          whileTap={{ scale: 0.9 }}
          whileHover={{ scale: 1.05 }}
          className="bg-[#2563eb] p-2 rounded-lg text-white hover:bg-[#1d4ed8] transition duration-150"
          onClick={handleSend}
        >
          <Send size={20} />
        </motion.button>
      </div>
    </div>
  );
};

export default ChatInput;
