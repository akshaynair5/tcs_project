import { useContext, useEffect, useState, useRef } from "react";
import MessageBox from "./messageBox";
import ChatInput from "./chatBar";
import { AuthContext } from "../contextProvider";
import axios from "axios";
import { motion } from "framer-motion";

const ChatComponent = () => {
  const { currentUser, currentChat } = useContext(AuthContext);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState(""); // ✨ NEW
  const messagesEndRef = useRef(null);
  const messageRefs = useRef([]); // To store references to each message
  const abortRef = useRef(null);

  useEffect(() => {
    if (currentChat && currentChat.messages) {
      setMessages(currentChat.messages);
      console.log(currentChat.messages);
    }
  }, [currentChat]);

  // Auto scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (input) => {
    if (!input.trim()) return;

    const tempId = Date.now().toString();
    const newMessage = { content: input, role: "user", id: tempId };
    setMessages((prev) => [...prev, newMessage]);
    setLoading(true);

    const controller = new AbortController();
    abortRef.current = { controller, id: tempId };

    try {
      const { data } = await axios.post(
        "http://127.0.0.1:5000/api/ask",
        {
          chat_id: currentChat._id,
          user_id: currentUser.user_id,
          question: input,
        },
        { signal: controller.signal }
      );

      const assistantMessage = { content: data.answer, role: "ai_assistant" };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      if (axios.isCancel(error)) {
        console.log("Request canceled");
      } else {
        const errorMessage = {
          content: error.response?.data?.error || "Something went wrong",
          role: "ai_assistant",
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    }

    setLoading(false);
  };

  const handleCancel = async () => {
    setLoading(false);

    setMessages((prevMessages) => {
      const updatedMessages = [...prevMessages];
      const lastMessage = updatedMessages.pop(); // Remove last message

      if (lastMessage && lastMessage._id) {
        axios
          .delete(`http://localhost:5000/api/messages/${lastMessage._id}`)
          .catch((err) => {
            console.error("Failed to delete message from DB:", err);
          });
      }

      return updatedMessages;
    });
  };

  // ✨ NEW: Filter messages based on search query
  const filteredMessages = messages.filter((msg) => {
    let textContent = "";

    if (msg.role === "user" && typeof msg.content === "string") {
      textContent = msg.content;
    } else if (msg.role === "ai_assistant" && typeof msg.content === "object") {
      textContent = msg.content.response_short || "";
    }

    return textContent.toLowerCase().includes(searchQuery.toLowerCase());
  });

  // Function to handle scroll to a specific message
  const handleScrollToMessage = (index) => {
    if (messageRefs.current[index]) {
      messageRefs.current[index].scrollIntoView({ behavior: "smooth" });
    }
  };

  // Clear the search and reset the filtered messages after clicking a message
  const handleMessageClick = (index) => {
    setSearchQuery(""); // Clear the search query when a message is clicked
    handleScrollToMessage(index); // Scroll to the clicked message
  };

  return (
    <div className="flex flex-col fixed left-[20vw] top-[10vh] w-[80vw] h-[90vh] bg-[#1a1a1e] px-4 pt-4 pb-24 overflow-y-auto">

      {/* ✨ Search Input */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search messages..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full p-2 rounded bg-[#2a2a2e] text-white placeholder-gray-400"
        />
      </div>

      {/* Message Area */}
      <div className="flex flex-col gap-4 overflow-y-auto text-white">
        {filteredMessages.map((msg, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
          >
            {/* Dummy div around MessageBox */}
            <div
              ref={(el) => (messageRefs.current[index] = el)} // Ref attached to the dummy div
              onClick={() => handleMessageClick(index)} // Reset search and scroll to message
            >
              <MessageBox
                content={msg.content}
                role={msg.role}
                chatId={currentChat._id}
                messageId={msg._id}
                userId={currentUser.user_id}
              />
            </div>
          </motion.div>
        ))}

        {loading && (
          <div className="text-center text-sm text-gray-400 animate-pulse">
            Typing...
          </div>
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
