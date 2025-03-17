import { useState } from "react";
import { Send } from "lucide-react";

const ChatInput = ({ onSend }) => {
  const [message, setMessage] = useState("");

  const handleSend = async () => {
    if (message.trim()) {
      await onSend(message);
      setMessage("");
    }
  };

  return (
    <div className="flex items-center gap-2 p-2 bg-white border-t border-gray-300 shadow-lg fixed bottom-2 w-[100vw] md:max-w-2xl mx-auto z-10">
      <input
        type="text"
        className="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        placeholder="Type your message..."
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSend()}
      />
      <button
        className="p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
        onClick={handleSend}
      >
        <Send size={20} />
      </button>
    </div>
  );
};

export default ChatInput;
