import { useContext, useEffect, useState, useRef } from "react";
import MessageBox from "./messageBox";
import ChatInput from "./chatBar";
import FileUpload from "./fileUpload";
import { AuthContext } from "../contextProvider";
import axios from "axios";
import { motion } from "framer-motion";

const ChatComponent = () => {
  const { currentUser, currentChat } = useContext(AuthContext);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (currentChat && currentChat.messages) {
      setMessages(currentChat.messages);
    }
  }, [currentChat]);

  // Auto scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (input) => {
    if (!input.trim()) return;

    const newMessage = { content: input, role: "user" };
    setMessages((prev) => [...prev, newMessage]);
    setLoading(true);

    try {
      const { data } = await axios.post("http://127.0.0.1:5000/api/ask", {
        chat_id: currentChat._id,
        user_id: currentUser.user_id,
        question: input,
      });

      const assistantMessage = { content: data.answer, role: "ai_assistant" };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage = {
        content: error.response?.data?.error || "Something went wrong",
        role: "ai_assistant",
      };
      setMessages((prev) => [...prev, errorMessage]);
    }

    setLoading(false);
  };

  return (
    <div className="flex flex-col fixed left-[20vw] top-[10vh] w-[80vw] h-[90vh] bg-[#1a1a1e] px-4 pt-4 pb-24 overflow-y-auto">
      {/* Message Area */}
      <div className="flex flex-col gap-4 overflow-y-auto text-white">
        {messages.map((msg, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
          >
            <MessageBox content={msg.content} role={msg.role} />
          </motion.div>
        ))}

        {loading && (
          <motion.div
            className="text-center text-sm text-gray-400 animate-pulse"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ repeat: Infinity, duration: 1 }}
          >
            Typing...
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Bottom Input Bar */}
      <div className="fixed bottom-4 flex justify-center bg-white">
        <div className="md:max-w-2xl flex gap-2 items-center">
          <ChatInput onSend={handleSend} />
        </div>
      </div>
    </div>
  );
};

export default ChatComponent;
